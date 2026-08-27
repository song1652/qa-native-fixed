"""
Step 6 -- Healer: 실패 테스트 자동 분석
LLM 없음. pytest를 상세 모드로 재실행해 실패 정보를 수집, state.json에 저장.
Claude Code가 heal_context를 읽고 test_generated.py를 직접 패치한 뒤 05_execute.py를 재실행한다.

종료 코드:
  EXIT_SUCCESS (0) = 모든 테스트 통과 (힐링 불필요)
  EXIT_HEAL_NEEDED (10) = 실패 정보 저장 완료 → Claude Code가 패치 필요
  EXIT_HEAL_EXCEEDED (2) = 최대 힐링 횟수 초과 (기본 3회) → 파이프라인 중단
"""
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from _python import PYTHON_EXE
from _paths import PIPELINE_STATE, read_state, update_state
from _constants import (
    EXIT_SUCCESS, EXIT_HEAL_NEEDED, EXIT_HEAL_EXCEEDED, MAX_HEAL,
    DEFAULT_GENERATED_DIR, DEFAULT_GENERATED_FILE,
    HEAL_PYTEST_WORKERS, PYTEST_HEAL_TIMEOUT_SEC,
)
from _pipeline_registry import Step  # P62: 문자열 리터럴 대신 Step 상수 사용
from heal_utils import (
    classify_error, extract_key_lines,  # noqa: F401 (re-export for tests)
    find_screenshot_for_test, append_lessons, update_heal_stats,
    build_heal_batches, print_heal_batches, MCP_SNAPSHOT_ERROR_TYPES,
    snapshot_assertions,
)
from structured_log import slog


def _detect_repeated_failures(
    current_failures: list[dict], prev_failures: list[dict]
) -> tuple[list[dict], list[dict]]:
    """이전 힐링과 동일한 테스트+에러 패턴이 반복되는 케이스를 분리한다.

    Returns:
        (healable, skipped): 힐링 대상과 스킵 대상 분리
    """
    if not prev_failures:
        return current_failures, []

    # 이전 실패의 (test_name, error_type) 집합
    # 이전 포맷에 error_type이 없으면 traceback에서 재분류
    prev_signatures = set()
    for f in prev_failures:
        etype = f.get("error_type") or classify_error(f.get("traceback", ""))
        sig = (f.get("test_name", ""), etype)
        prev_signatures.add(sig)

    healable = []
    skipped = []
    for f in current_failures:
        error_type = classify_error(f["traceback"])
        f["error_type"] = error_type
        sig = (f.get("test_name", ""), error_type)
        if sig in prev_signatures:
            skipped.append(f)
        else:
            healable.append(f)

    return healable, skipped


def parse_failures(output: str, file_path: str) -> list[dict]:
    """pytest --tb=long 출력에서 실패 케이스별 정보를 추출한다.

    두 가지 패턴으로 수집:
    1. FAILED 줄에서 test_id/test_name 추출
    2. '_ test_name _' 구분선과 'FAILED' 줄 사이의 traceback 블록 매칭
    """
    failures = []

    # 패턴 1: '_ test_xxx _' ~ 'FAILED ...' 사이 traceback 블록 수집
    lines = output.splitlines()
    current = None
    for line in lines:
        # traceback 블록 시작: _____ test_xxx _____
        if re.match(r'^_{3,}\s+(test_\w+)\s+_{3,}$', line.strip()):
            match = re.match(r'^_{3,}\s+(test_\w+)\s+_{3,}$', line.strip())
            current = {"test_id": "", "test_name": match.group(1), "traceback": []}
            continue

        # FAILED 줄: 블록 종료 + test_id 업데이트
        if line.startswith("FAILED ") and "::" in line:
            test_id = line.split("FAILED ", 1)[1].strip()
            test_name = test_id.split("::")[-1]
            if current and current["test_name"] == test_name:
                current["test_id"] = test_id
                current["traceback"] = "\n".join(current["traceback"])
                failures.append(current)
                current = None
            elif current:
                current["traceback"] = "\n".join(current["traceback"])
                failures.append(current)
                current = None
                failures.append({"test_id": test_id, "test_name": test_name, "traceback": ""})
            else:
                failures.append({"test_id": test_id, "test_name": test_name, "traceback": ""})
            continue

        # '= short test summary info =' 줄 이후는 수집 중단
        if "short test summary info" in line:
            if current:
                current["traceback"] = "\n".join(current["traceback"])
                failures.append(current)
                current = None
            continue

        if current is not None:
            current["traceback"].append(line)

    if current:
        current["traceback"] = "\n".join(current["traceback"])
        failures.append(current)

    return failures


def collect_failure_details_from_report(state: dict) -> tuple[list[dict], str]:
    """05_execute가 생성한 JSON report에서 실패 정보를 파싱한다 (pytest 재실행 없음)."""
    import json as _json
    json_report_path = state.get("execution_result", {}).get("json_report_path", "")
    if json_report_path and Path(json_report_path).exists():
        try:
            report = _json.loads(Path(json_report_path).read_text(encoding="utf-8"))
            failures = []
            raw_lines = []
            for test in report.get("tests", []):
                if test.get("outcome") in ("failed", "error"):
                    nodeid = test.get("nodeid", "")
                    test_name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
                    # call 단계의 longrepr (traceback)
                    longrepr = ""
                    call = test.get("call", {})
                    longrepr = call.get("longrepr", "")
                    if not longrepr:
                        # setup/teardown 에러
                        for phase in ("setup", "teardown"):
                            p = test.get(phase, {})
                            if p.get("longrepr"):
                                longrepr = p["longrepr"]
                                break
                    failures.append({
                        "test_id": nodeid,
                        "test_name": test_name,
                        "traceback": longrepr,
                    })
                    raw_lines.append(f"FAILED {nodeid}")
                    if longrepr:
                        raw_lines.append(longrepr[:500])
            return failures, "\n".join(raw_lines)
        except Exception:
            pass
    # JSON report가 없으면 fallback: 실패 테스트만 재실행
    return _collect_failure_details_fallback(
        state.get("generated_file_path", DEFAULT_GENERATED_DIR)
    )


def _collect_failure_details_fallback(file_path: str) -> tuple[list[dict], str]:
    """Fallback: JSON report 없을 때 실패 테스트만 재실행하여 정보 수집."""
    try:
        cmd = [PYTHON_EXE, "-m", "pytest", file_path,
               "--tb=long", "-v", "--no-header", "--lf"]
        if Path(file_path).is_dir():
            cmd += [f"-n{HEAL_PYTEST_WORKERS}", "--dist=load"]
        result = subprocess.run(
            cmd,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=PYTEST_HEAL_TIMEOUT_SEC,
        )
        output = result.stdout + result.stderr
        if "no tests ran" in output or "collected 0 items" in output:
            cmd_full = [c for c in cmd if c != "--lf"]
            result = subprocess.run(
                cmd_full,
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                timeout=PYTEST_HEAL_TIMEOUT_SEC,
            )
            output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output = f"[06] pytest 실행 타임아웃 ({PYTEST_HEAL_TIMEOUT_SEC}초 초과)"
    failures = parse_failures(output, file_path)
    return failures, output


def main():
    state_path = PIPELINE_STATE
    if not state_path.exists():
        print("[오류] state/pipeline.json 없음.")
        sys.exit(1)

    state = read_state(state_path)

    execution_result = state.get("execution_result", {})
    if execution_result.get("failed", 0) == 0 and execution_result.get("exit_code", 1) == 0:
        print("[06] 모든 테스트 통과 - 힐링 불필요.")
        slog("heal_skip_all_pass", step="06_heal")
        # pytest 재실행 없이 기존 결과로 리포트만 생성
        import importlib.util
        _spec = importlib.util.spec_from_file_location(
            "execute_05", Path(__file__).parent / "05_execute.py"
        )
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        _mod.generate_report_from_state(state_path)
        sys.exit(EXIT_SUCCESS)

    # 힐링 횟수 확인
    heal_count = state.get("heal_count", 0)
    if heal_count >= MAX_HEAL:
        print(f"[06] 최대 힐링 횟수({MAX_HEAL}회) 초과. 파이프라인을 중단합니다.")
        update_state(state_path, lambda fresh: {**fresh, "step": Step.HEAL_FAILED})
        sys.exit(EXIT_HEAL_EXCEEDED)

    # 힐링 전 사이트 접근 가능 체크
    url = state.get("url", "")
    if url:
        import urllib.request
        import urllib.error
        try:
            # GET 사용: HEAD를 405/403으로 거부하는 서버가 있어 오탐이 났다.
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.getcode()
            if status >= 400:
                print(f"[06] 사이트 접근 불가: {url} (HTTP {status})")
                print("     사이트가 다운되었거나 접근이 차단되었습니다. 힐링을 건너뜁니다.")
                _ctx = {"error": f"사이트 접근 불가 HTTP {status}", "url": url}
                update_state(state_path, lambda fresh: {**fresh, "step": Step.HEAL_FAILED, "heal_context": _ctx})
                sys.exit(EXIT_HEAL_EXCEEDED)
        except (urllib.error.URLError, OSError) as e:
            print(f"[06] 사이트 접근 불가: {url} ({e})")
            print("     사이트가 다운되었거나 네트워크 문제입니다. 힐링을 건너뜁니다.")
            _ctx = {"error": f"사이트 접근 불가: {e}", "url": url}
            update_state(state_path, lambda fresh: {**fresh, "step": Step.HEAL_FAILED, "heal_context": _ctx})
            sys.exit(EXIT_HEAL_EXCEEDED)

    file_path = state.get("generated_file_path", DEFAULT_GENERATED_FILE)
    if not Path(file_path).exists():
        print(f"[오류] 테스트 파일 없음: {file_path}")
        sys.exit(1)

    slog("step_start", step="06_heal", heal_round=heal_count + 1, max_heal=MAX_HEAL)
    print(f"[06] 실패 분석 중 (힐링 {heal_count + 1}/{MAX_HEAL}회차)...")
    print()

    failures, raw_output = collect_failure_details_from_report(state)

    # 실패가 파싱되지 않은 경우 raw 출력 전체 저장
    if not failures and execution_result.get("exit_code", 0) != 0:
        failures = [{"test_id": "unknown", "test_name": "unknown", "traceback": raw_output[-3000:]}]

    # 각 failure에 스크린샷 경로 연결 (힐링 시 시각 검증용)
    for f in failures:
        f["screenshot"] = find_screenshot_for_test(f["test_name"])

    # 동일 오류 2회 연속 반복 감지 → 해당 테스트 스킵
    prev_heal_context = state.get("heal_context") or {}
    prev_failures = prev_heal_context.get("failures", [])
    healable, skipped = _detect_repeated_failures(failures, prev_failures)

    if skipped:
        skipped_names = [f["test_name"] for f in skipped]
        for s in skipped:
            slog("heal_skip_repeated", test_name=s["test_name"], error_type=s.get("error_type", ""))
        print(f"[06] 동일 오류 2회 연속 반복 → {len(skipped)}건 스킵:")
        for name in skipped_names:
            print(f"     - {name}")
        print()

    # 스킵 후 힐링 대상이 없으면 heal_failed로 종료
    if not healable and skipped:
        print("[06] 모든 실패가 반복 패턴 -- 수동 수정이 필요합니다.")
        _ctx = {
            "heal_count": heal_count + 1,
            "skipped_repeated": [f["test_name"] for f in skipped],
            "error": "모든 실패가 동일 오류 2회 반복. 수동 수정 필요.",
            "analyzed_at": datetime.now().isoformat(),
        }
        update_state(state_path, lambda fresh: {**fresh, "step": Step.HEAL_FAILED, "heal_context": _ctx})
        sys.exit(EXIT_HEAL_EXCEEDED)

    # 에러 타입별 그룹핑 (Agent가 같은 유형 일괄 처리 가능)
    from collections import defaultdict
    failure_groups = defaultdict(list)
    for f in healable:
        if "error_type" not in f:
            f["error_type"] = classify_error(f["traceback"])
        failure_groups[f["error_type"]].append(f["test_name"])

    needs_mcp = any(f.get("error_type", "") in MCP_SNAPSHOT_ERROR_TYPES for f in healable)
    heal_context = {
        "heal_count": heal_count + 1,
        "failure_count": len(healable),
        "failures": healable,
        "failure_groups": dict(failure_groups),
        "skipped_repeated": [f["test_name"] for f in skipped],
        "url": state.get("url", ""),
        "raw_tail": raw_output[-2000:],
        "analyzed_at": datetime.now().isoformat(),
        "mcp_snapshot_recommended": needs_mcp,
        "mcp_snapshot_url": state.get("url", "") if needs_mcp else "",
    }

    # 패치 전 assertion 스냅샷 저장 (assert_guard.py가 직전 패치 기준 비교에 사용)
    failing_files = list({
        str(Path(f["test_id"].split("::")[0]))
        for f in healable if "::" in f.get("test_id", "")
    })
    if not failing_files:
        # test_id에 경로가 없으면 generated_file_path 디렉토리에서 추론
        gen_path = Path(file_path)
        if gen_path.is_dir():
            failing_files = [str(gen_path / (f["test_name"] + ".py")) for f in healable]
        else:
            failing_files = [str(gen_path)]
    pre_heal_assertions = snapshot_assertions(failing_files)
    _new_heal_count = heal_count + 1  # 표시·slog 용 로컬 값

    def _mutator(fresh: dict) -> dict:
        # P70: heal_count는 fresh 기준으로 증가 (RMW 경쟁 방지).
        # read_state 이후 다른 프로세스(병렬 subagent 등)가 heal_count를 먼저
        # 증가시켰을 경우, 캡처된 _new_heal_count로 덮어쓰면 카운터가 리셋된다.
        updated = {
            **fresh,
            "pre_heal_assertions": pre_heal_assertions,
            "heal_context": heal_context,
            "heal_count": fresh.get("heal_count", 0) + 1,
            "step": Step.HEAL_NEEDED,
        }
        # original_assertions: 최초 생성 시점 기준으로 고정 (이후 라운드에서 덮어쓰지 않음).
        # "설정되어 있는지" 여부는 최신 상태(fresh) 기준으로 판단해야
        # 동시에 다른 프로세스가 먼저 설정한 값을 덮어쓰지 않는다.
        if not fresh.get("original_assertions"):
            updated["original_assertions"] = pre_heal_assertions
        return updated

    update_state(state_path, _mutator)

    # 실수 패턴 자동 기록 (healable + skipped 모두 기록)
    append_lessons(healable + skipped)

    # heal_stats.json 빈도 카운터 업데이트
    update_heal_stats(healable + skipped)

    print(f"[06] 힐링 대상: {len(healable)}건" +
          (f", 반복 스킵: {len(skipped)}건" if skipped else ""))

    # 배치 분할 + 병렬 힐링 지시 출력
    batches = build_heal_batches(healable)
    print_heal_batches(batches, url=state.get("url", ""), pipeline="single")
    slog("step_end", step="06_heal", healable=len(healable),
         skipped=len(skipped), heal_round=heal_count + 1)
    sys.exit(EXIT_HEAL_NEEDED)


if __name__ == "__main__":
    main()
