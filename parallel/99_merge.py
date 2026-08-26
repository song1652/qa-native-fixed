"""
병렬 파이프라인 Step 99 - 실행 + 통합 리포트

1. tests/generated/ 에서 pytest 일괄 실행 (JSON 리포트)
2. 실패 시 heal_context 저장 → Claude Code 힐링 루프 (최대 3회)
3. 그룹별 PASS/FAIL 집계
4. HTML 리포트 생성 (tests/reports/parallel_index_{ts}.html)

LLM 없음. 순수 Python.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

_SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
from _paths import (
    PROJECT_ROOT, PARALLEL_STATE, HEAL_CONTEXT_STATE, PIPELINE_STATE, QUICK_STATE,
    read_state, write_state, update_state, append_run_history,
)
from _python import PYTHON_EXE
from _constants import MAX_HEAL
from _pipeline_registry import ParallelStatus
from heal_utils import (
    classify_error, extract_key_lines,
    find_screenshot_for_test, append_lessons, update_heal_stats,
    build_heal_batches, print_heal_batches,
    LESSONS_PATH, LESSONS_AUTO_PATH,
    snapshot_assertions, compare_assertions,
)
from report_html import case_row as _case_row, build_report
from result_parser import parse_results, parse_skip_messages
from structured_log import slog
try:
    from parse_cases import load_cases as _load_cases
except ImportError:
    _load_cases = None

GENERATED_DIR = PROJECT_ROOT / "tests" / "generated"
TESTCASES_DIR = PROJECT_ROOT / "testcases"
SCREENSHOTS_DIR = PROJECT_ROOT / "tests" / "screenshots"


def _natural_sort_key(p: Path) -> list:
    """파일명을 숫자 기준으로 정렬하는 키 (tc_10 > tc_9 보장)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", p.name)]


# ── 상태 업데이트 헬퍼 ──────────────────────────────────────────


def _update_parallel_status(
    status: str,
    extra: dict | None = None,
    *,
    path: "Path | None" = None,
) -> None:
    """state/parallel.json(또는 path)의 status 필드를 업데이트 (기존 데이터 보존).

    락 보유 중 최신 상태를 읽어 병합·쓰기까지 원자적으로 수행해, 다른
    프로세스가 그 사이 쓴 필드를 덮어쓰지 않는다(RMW 경쟁 방지).

    Args:
        status: 설정할 새 status 값.
        extra:  추가로 병합할 필드 딕셔너리.
        path:   상태 파일 경로. None이면 PARALLEL_STATE(state/parallel.json).
                quick 모드에서는 QUICK_STATE를 전달한다 (P41 FSM 크래시 수정).
    """
    def _mutator(fresh: dict) -> dict:
        updated = {**fresh, "status": status}
        if extra:
            updated.update(extra)
        return updated

    update_state(path or PARALLEL_STATE, _mutator)


# ── pytest 실행 ──────────────────────────────────────────────────


def _check_urls_accessible(urls: dict) -> dict | None:
    """힐링 전 사이트 접근 가능 여부를 사전 체크. 접근 불가 시 에러 dict 반환."""
    import urllib.request
    import urllib.error
    for group, url in urls.items():
        if not url:
            continue
        try:
            # GET 사용: HEAD를 405/403으로 거부하는 서버가 있어 오탐이 났다.
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.getcode()
            if status >= 400:
                return {"error": f"사이트 접근 불가 HTTP {status}", "url": url, "group": group}
        except (urllib.error.URLError, OSError) as e:
            return {"error": f"사이트 접근 불가: {e}", "url": url, "group": group}
    return None


def _detect_repeated_failures_parallel(
    current_failures: list[dict], prev_ctx: dict
) -> tuple[list[dict], list[dict]]:
    """이전 heal_context와 비교하여 동일 (test_name, error_type) 반복 감지.

    Returns:
        (healable, skipped)
    """
    prev_failures = prev_ctx.get("failures", [])
    if not prev_failures:
        return current_failures, []

    prev_signatures = set()
    for f in prev_failures:
        etype = f.get("error_type") or classify_error(f.get("traceback", ""))
        prev_signatures.add((f.get("test_name", ""), etype))

    healable, skipped = [], []
    for f in current_failures:
        sig = (f.get("test_name", ""), f.get("error_type", ""))
        if sig in prev_signatures:
            skipped.append(f)
        else:
            healable.append(f)
    return healable, skipped


def build_heal_context(report: dict, heal_count: int, state_path: Path) -> dict | None:
    """실패 테스트의 traceback을 모아 heal_context.json 생성. 실패 없으면 None 반환.

    단일 파이프라인(06_heal.py)과 동일한 플로우:
    1. 실패 수집 + 스크린샷 연결
    2. classify_error로 에러 분류 + failure_groups 구성
    3. 사이트 사전 접근 체크
    4. 반복 실패 감지 (_detect_repeated_failures_parallel)
    5. append_lessons + update_heal_stats
    6. 힐링 전 assertion 스냅샷 저장 (state_path에 pre_heal_assertions/original_assertions)
    """
    failures = []
    for t in report.get("tests", []):
        if t.get("outcome") in ("failed", "error"):
            call = t.get("call") or {}
            longrepr = call.get("longrepr", "")
            if isinstance(longrepr, dict):
                longrepr = longrepr.get("reprcrash", {}).get("message", str(longrepr))
            test_name = t.get("nodeid", "").split("::")[-1]
            traceback_str = str(longrepr)
            failures.append({
                "test_id": t.get("nodeid", ""),
                "test_name": test_name,
                "file": t.get("nodeid", "").split("::")[0],
                "traceback": traceback_str,
                "error_type": classify_error(traceback_str),
                "screenshot": find_screenshot_for_test(test_name),
            })
    if not failures:
        return None

    # 실패 그룹의 URL 수집 (pages.json에서)
    urls = {}
    pages_path = PROJECT_ROOT / "config" / "pages.json"
    if pages_path.exists():
        try:
            pages_data = json.loads(pages_path.read_text(encoding="utf-8"))
            for f in failures:
                group = f["file"].split("/")[-2] if "/" in f["file"] else None
                if group and group in pages_data and group not in urls:
                    entry = pages_data[group]
                    urls[group] = entry.get("url") if isinstance(entry, dict) else entry
        except Exception:
            pass

    # 사이트 접근 가능성 사전 체크
    if urls:
        site_err = _check_urls_accessible(urls)
        if site_err:
            print(f"\n[99] 사이트 접근 불가: {site_err['url']} ({site_err['error']})")
            print("     사이트가 다운되었거나 네트워크 문제입니다. 힐링을 건너뜁니다.")
            ctx = {
                "heal_count": heal_count,
                "error": site_err["error"],
                "url": site_err["url"],
                "analyzed_at": datetime.now().isoformat(),
            }
            write_state(HEAL_CONTEXT_STATE, ctx)
            return None  # 힐링 불가 → 호출부에서 heal_failed 처리

    # 에러 타입별 그룹핑
    failure_groups = defaultdict(list)
    for f in failures:
        failure_groups[f["error_type"]].append(f["test_name"])

    # 반복 실패 감지
    prev_ctx = read_state(HEAL_CONTEXT_STATE)
    healable, skipped = _detect_repeated_failures_parallel(failures, prev_ctx)

    if skipped:
        skipped_names = [f["test_name"] for f in skipped]
        print(f"\n[99] 동일 오류 2회 연속 반복 → {len(skipped)}건 스킵:")
        for name in skipped_names:
            print(f"     - {name}")
        for s in skipped:
            slog("heal_skip_repeated", test_name=s["test_name"],
                 error_type=s.get("error_type", ""), pipeline="parallel")

    # 모든 실패가 반복 → 힐링 중단
    if not healable and skipped:
        print("[99] 모든 실패가 반복 패턴 -- 수동 수정이 필요합니다.")
        ctx = {
            "heal_count": heal_count,
            "skipped_repeated": [f["test_name"] for f in skipped],
            "error": "모든 실패가 동일 오류 2회 반복. 수동 수정 필요.",
            "analyzed_at": datetime.now().isoformat(),
        }
        write_state(HEAL_CONTEXT_STATE, ctx)
        append_lessons(failures)
        update_heal_stats(failures)
        return None

    # 최신 lessons_learned 스냅샷 (subagent 간 학습 공유)
    lessons_snapshot = ""
    for lpath in [LESSONS_PATH, LESSONS_AUTO_PATH]:
        if lpath.exists():
            try:
                lessons_snapshot += lpath.read_text(encoding="utf-8") + "\n"
            except Exception:
                pass

    ctx = {
        "heal_count": heal_count,
        "failure_count": len(healable),
        "failures": healable,
        "failure_groups": dict(failure_groups),
        "skipped_repeated": [f["test_name"] for f in skipped],
        "urls": urls,
        "lessons_snapshot": lessons_snapshot[-3000:] if lessons_snapshot else "",
        "analyzed_at": datetime.now().isoformat(),
    }
    write_state(HEAL_CONTEXT_STATE, ctx)
    print(f"\n[99] heal_context 저장됨: {HEAL_CONTEXT_STATE}  "
          f"(힐링 대상 {len(healable)}건"
          + (f", 반복 스킵 {len(skipped)}건" if skipped else "") + ")")

    # 실수 패턴 자동 기록 + heal_stats 빈도 업데이트
    append_lessons(healable + skipped)
    update_heal_stats(healable + skipped)

    # 힐링 전 assertion 스냅샷 저장 (06_heal.py와 동일한 정책)
    # pre_heal_assertions: 직전 패치 기준 / original_assertions: 최초 힐링 라운드 기준(고정)
    failing_files = sorted({
        str(f["file"]) if Path(f["file"]).is_absolute() else str(PROJECT_ROOT / f["file"])
        for f in healable if f.get("file")
    })
    pre_snap = snapshot_assertions(failing_files)

    def _snap_mutator(fresh: dict) -> dict:
        updated = {
            **fresh,
            "pre_heal_assertions": pre_snap,
            "pre_heal_files": failing_files,
        }
        if not fresh.get("original_assertions"):
            updated["original_assertions"] = pre_snap
        return updated

    update_state(state_path, _snap_mutator)

    return ctx


def _try_auto_heal(state_path: "Path | None" = None) -> bool:
    """06_auto_heal.py를 subprocess로 호출하여 deterministic 패치 시도 (P53).

    Args:
        state_path: 힐링 상태 파일 경로. None이면 단일 파이프라인 기본값
                    (state/pipeline.json). 병렬 파이프라인에서는
                    PARALLEL_STATE_PATH를 전달해야 한다.

    Returns:
        True: auto_heal이 일부/전부 패치 성공 (재실행 필요)
        False: 자동 패치 가능한 패턴 없음 (Agent 힐링 필요)
    """
    auto_heal_script = PROJECT_ROOT / "scripts" / "06_auto_heal.py"
    if not auto_heal_script.exists():
        return False
    cmd = [PYTHON_EXE, str(auto_heal_script)]
    if state_path is not None:
        cmd += ["--state-path", str(state_path)]
        # parallel.json / quick.json은 status 키를 사용
        if state_path.name in ("parallel.json", "quick.json"):
            cmd += ["--state-key", "status"]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True,
            timeout=120,
        )
        # 출력 표시
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                print(f"  {line}")
        # 종료코드 0 = 모든 실패 자동 수정 완료
        # 종료코드 1 = 일부 실패 남음, 3 = 스킵 (heal_needed 아님)
        # exit 3 (스킵)은 "자동 완료"가 아니므로 False 반환
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"  [auto_heal] 실행 실패 (무시): {e}")
        return False


def print_heal_instructions(heal_context: dict, pipeline: str = "parallel") -> None:
    """배치 분할 병렬 힐링 지시를 출력."""
    failures = heal_context.get("failures", [])
    urls = heal_context.get("urls", {})
    # URL 하나로 통합 (여러 그룹이면 첫 번째)
    url = next(iter(urls.values()), "") if urls else ""

    batches = build_heal_batches(failures)
    print_heal_batches(batches, url=url, pipeline=pipeline)


def verify_lessons_learned_updated(heal_start_time: str) -> bool:
    """힐링 후 lessons_learned.md가 업데이트되었는지 검증.

    heal_start_time 이후에 lessons_learned.md가 수정되었는지 확인.
    누락 시 경고 출력, 반환값은 업데이트 여부.
    """
    if not LESSONS_PATH.exists():
        return False
    from datetime import datetime as dt
    try:
        start = dt.fromisoformat(heal_start_time)
        mtime = dt.fromtimestamp(LESSONS_PATH.stat().st_mtime)
        if mtime > start:
            return True
    except Exception:
        pass
    print()
    print("⚠ [경고] lessons_learned.md 기록이 누락되었습니다!")
    print("  힐링 패치 후 반드시 agents/lessons_learned.md에 기록해야 합니다.")
    print("  형식: ### [힐링] {날짜} -- {파일명}")
    print("        - **문제**: {traceback 요약}")
    print("        - **수정**: {적용한 패치 내용}")
    print("        - **재발 방지**: {동일 실수 방지 규칙}")
    print()
    return False


# ── HTML 리포트 ──────────────────────────────────────────────────


def _load_cases_for_group(group_name: str) -> list:
    """testcases/{group_name}/ 에서 케이스 메타데이터 로드."""
    if not _load_cases:
        return []
    group_dir = TESTCASES_DIR / group_name
    if group_dir.is_dir():
        return _load_cases(str(group_dir))
    return []


def _scan_generated_groups() -> dict[str, list[Path]]:
    """tests/generated/ 하위 그룹별 파일 목록 반환 (자연 정렬)."""
    groups: dict[str, list[Path]] = defaultdict(list)
    if not GENERATED_DIR.exists():
        return groups
    for group_dir in sorted(GENERATED_DIR.iterdir(), key=_natural_sort_key):
        if not group_dir.is_dir() or group_dir.name.startswith("."):
            continue
        for f in sorted(
            (f for f in group_dir.glob("*.py")
             if f.name not in ("conftest.py", "__init__.py")),
            key=_natural_sort_key,
        ):
            groups[group_dir.name].append(f)
    return groups


def build_html(test_results: dict, summary: dict,
               created_at: str, target_groups: list[str] | None = None,
               skip_messages: dict | None = None) -> str:
    skip_messages = skip_messages or {}
    groups = _scan_generated_groups()
    if target_groups:
        groups = {k: v for k, v in groups.items() if k in target_groups}

    groups_data = []
    for label, files in groups.items():
        group_tests = {
            k: v for k, v in test_results.items()
            if f"/{label}/" in k or f"\\{label}\\" in k
        }
        g_pass_cnt = sum(1 for v in group_tests.values() if v == "passed")
        g_skip_cnt = sum(1 for v in group_tests.values() if v == "skipped")
        g_total_cnt = len(group_tests)
        g_passed = not any(v == "failed" for v in group_tests.values()) if group_tests else False

        cases = _load_cases_for_group(label)
        rows_html = ""
        if cases:
            for case_idx, case in enumerate(cases):
                uid = f"{label}_{case_idx}"
                case_id = case.get("id", "")
                matched_nodeid = next(
                    (k for k in group_tests
                     if case_id and (f"/{case_id}." in k or f"/{case_id}_" in k)),
                    None,
                )
                case_outcome = group_tests.get(matched_nodeid, "failed") if matched_nodeid else "failed"
                if case_outcome == "skipped" and matched_nodeid and matched_nodeid in skip_messages:
                    case = dict(case, skip_reason=skip_messages[matched_nodeid])
                rows_html += _case_row(case, uid, case_outcome)
        else:
            for file_idx, f in enumerate(sorted(files, key=_natural_sort_key)):
                uid = f"{label}_{file_idx}"
                nodeid_match = next(
                    (k for k in test_results if f.stem in k), None
                )
                outcome = test_results.get(nodeid_match, "failed") if nodeid_match else "failed"
                simple_case = {
                    "title": f.stem.replace("_", " ").title(),
                    "precondition": "", "steps": [], "expected": "",
                }
                if outcome == "skipped" and nodeid_match and nodeid_match in skip_messages:
                    simple_case["skip_reason"] = skip_messages[nodeid_match]
                rows_html += _case_row(simple_case, uid, outcome)

        if not rows_html:
            rows_html = '<p class="empty-msg">케이스 정보 없음</p>'

        groups_data.append({
            "label": label, "rows_html": rows_html,
            "pass_cnt": g_pass_cnt, "total_cnt": g_total_cnt,
            "all_pass": g_passed, "has_tests": bool(group_tests),
            "skip_cnt": g_skip_cnt,
        })

    return build_report(groups_data, summary, created_at, "Parallel Test Report")


# ── 메인 ────────────────────────────────────────────────────────


def main():
    import argparse
    import tempfile
    parser = argparse.ArgumentParser(description="QA 테스트 실행 + 리포트 생성")
    parser.add_argument(
        "--group", "-g",
        nargs="*",
        metavar="FOLDER",
        help="실행할 폴더명 (예: login checkout). 생략 시 전체 실행."
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="빠른 실행 모드: state/quick.json에 결과 저장 (parallel_state 미변경)"
    )
    parser.add_argument(
        "--no-heal", action="store_true",
        help="힐링 단계 생략: 실패해도 heal_context를 생성하지 않음"
    )
    args = parser.parse_args()
    import time as _time
    _start_time = _time.monotonic()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. 실행 대상 결정 + 자연 정렬
    def _valid_py_files(group_dir: Path) -> list:
        """testcases/{group}/tc_*.md 기준으로 유효한 .py 파일만 반환 (잔여 파일 제외).
        번호 prefix(tc_01_)로 매칭 — 슬러그 명명 차이 무관하게 동작.
        """
        import re as _re
        def _tc_num(name: str):
            m = _re.match(r"tc_(\d+)_", name)
            return m.group(1) if m else None

        tc_dir = TESTCASES_DIR / group_dir.name
        if tc_dir.exists():
            valid_nums = {_tc_num(f.name) for f in tc_dir.glob("tc_*.md")} - {None}
            all_py = list(group_dir.glob("tc_*.py"))
            files = [f for f in all_py if _tc_num(f.name) in valid_nums]
            stale = [f for f in all_py if _tc_num(f.name) not in valid_nums]
            if stale:
                print(f"[99] 잔여 파일 {len(stale)}개 제외 ({group_dir.name}): {', '.join(f.name for f in stale[:5])}{'...' if len(stale) > 5 else ''}")
        else:
            files = [f for f in group_dir.glob("*.py") if f.name not in ("conftest.py", "__init__.py")]
        return files

    if args.group:
        target_dirs = [GENERATED_DIR / g for g in args.group]
        missing = [str(d) for d in target_dirs if not d.exists()]
        if missing:
            print(f"[오류] 존재하지 않는 폴더: {', '.join(missing)}")
            available = [d.name for d in GENERATED_DIR.iterdir() if d.is_dir()]
            print(f"  사용 가능한 폴더: {', '.join(available) or '없음'}")
            return
        raw_files = []
        for d in target_dirs:
            raw_files.extend(_valid_py_files(d))
        scope_label = ", ".join(args.group)
    else:
        raw_files = []
        if GENERATED_DIR.exists():
            for d in GENERATED_DIR.iterdir():
                if d.is_dir() and not d.name.startswith((".", "_")):
                    raw_files.extend(_valid_py_files(d))
        scope_label = "전체"

    # 자연 정렬: tc_9 < tc_10 < tc_11 (문자열 정렬 버그 방지)
    sorted_files = sorted(raw_files, key=_natural_sort_key)

    if not sorted_files:
        print("[오류] 실행할 테스트 파일 없음.")
        if GENERATED_DIR.exists():
            available = [d.name for d in GENERATED_DIR.iterdir() if d.is_dir()]
            if available:
                print(f"  사용 가능한 폴더: {', '.join(available)}")
                print(f"  예시: python parallel/99_merge.py --group {available[0]}")
        return

    quick_mode = args.quick
    slog("step_start", step="99_merge", scope=scope_label,
         file_count=len(sorted_files), quick=quick_mode)
    print(f"\n[99] 실행 범위: {scope_label}  ({len(sorted_files)}개 케이스, 순차 실행)")

    # 2. pytest 실행 전 스크린샷 정리 (최종 실패 시만 남기기)
    if SCREENSHOTS_DIR.exists():
        shutil.rmtree(SCREENSHOTS_DIR, ignore_errors=True)

    # --quick 플래그만 quick mode (state/quick.json 사용)
    # --group 단독 사용 시에는 parallel.json 업데이트
    state_path = QUICK_STATE if quick_mode else PARALLEL_STATE

    # pytest 실행 시작 전 status를 "testing"으로 설정 (P41 FSM 크래시 수정).
    # quick 모드도 포함: quick.json이 이전 실행의 done/heal_needed/heal_failed 상태일 때
    # 최종 결과(done|heal_needed|heal_failed)로 직접 전이하면 FSM이 ValueError를 냈다.
    # done→testing→(done|heal_needed|heal_failed) 경로를 거치면 기존 FSM 전이표로 해결됨.
    _update_parallel_status(ParallelStatus.TESTING, path=state_path)

    # heal_count는 병렬 상태 파일(state_path)에서 읽기 (단일 파이프라인 오염 방지)
    heal_count = 0
    heal_analyzed_at = None
    _parallel_st = read_state(state_path)
    heal_count = _parallel_st.get("heal_count", 0)
    # lessons_learned 검증용 analyzed_at은 heal_context.json에서만 읽기
    _prev_ctx = read_state(HEAL_CONTEXT_STATE)
    if _prev_ctx:
        heal_analyzed_at = _prev_ctx.get("analyzed_at")

    # 힐링 재실행 시 lessons_learned 기록 검증
    if heal_count > 0 and heal_analyzed_at:
        verify_lessons_learned_updated(heal_analyzed_at)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_report_path = Path(tempfile.gettempdir()) / f"qa_report_{ts}.json"

    # 자연 정렬된 파일 경로를 직접 pytest에 전달 → 순차 실행 보장
    # Windows 커맨드라인 길이 제한(~32KB) 초과 방지: 파일 수가 많으면 runner 스크립트 사용
    import tempfile as _tempfile
    _runner_script = None
    try:
        file_args = [str(f) for f in sorted_files]
        cmd_len = sum(len(f) + 1 for f in file_args)
        if cmd_len > 20000:
            # 임시 Python 스크립트로 pytest.main() 직접 호출 → 커맨드라인 길이 제한 우회
            _json_report_str = str(json_report_path).replace("\\", "\\\\")
            runner_code = (
                "import sys, pytest\n"
                f"files = {file_args!r}\n"
                "args = files + [\n"
                "    '--json-report',\n"
                f"    '--json-report-file={_json_report_str}',\n"
                "    '--tb=short', '-v',\n"
                "]\n"
                "sys.exit(pytest.main(args))\n"
            )
            _af = _tempfile.NamedTemporaryFile(mode="w", suffix="_pytest_runner.py", delete=False, encoding="utf-8")
            _af.write(runner_code)
            _af.close()
            _runner_script = Path(_af.name)
            cmd = [PYTHON_EXE, str(_runner_script)]
            print(f"[99] 파일 수 {len(sorted_files)}개 — runner 스크립트 방식으로 pytest 실행")
        else:
            cmd = [PYTHON_EXE, "-m", "pytest"] + file_args + [
                "--json-report",
                f"--json-report-file={json_report_path}",
                "--tb=short", "-v",
            ]
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=False,
            timeout=7200,
        )
        pytest_exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        print("\n[99] pytest 실행 타임아웃 (7200초 초과)")
        pytest_exit_code = -1
    finally:
        if _runner_script and _runner_script.exists():
            _runner_script.unlink(missing_ok=True)
    report = {}
    if json_report_path.exists():
        report = json.loads(json_report_path.read_text(encoding="utf-8"))
        json_report_path.unlink()

    # 3. 결과 파싱
    test_results = parse_results(report)  # {nodeid: "passed"|"failed"|"skipped"}
    pytest_summary = report.get("summary", {})

    # 3-b. 실패 판정: pytest 종료코드 + JSON 리포트 모두 확인
    #      collection error 등은 JSON summary에 안 잡히므로 종료코드로 보완
    failed_count = pytest_summary.get("failed", 0) + pytest_summary.get("error", 0)
    has_issues = pytest_exit_code != 0 or failed_count > 0
    if has_issues:
        if args.no_heal:
            print(f"\n[99] 실패 {failed_count}건 -- 힐링 생략 (--no-heal)")
            HEAL_CONTEXT_STATE.unlink(missing_ok=True)
        elif heal_count >= MAX_HEAL:
            print(f"\n[99] 최대 힐링 횟수({MAX_HEAL}회) 초과 -- 수동 수정이 필요합니다.")
            HEAL_CONTEXT_STATE.unlink(missing_ok=True)
            # heal_count + heal_failed를 병렬 상태 파일에 반영 (단일 파이프라인 오염 방지)
            update_state(state_path, lambda fresh: {
                **fresh, "heal_count": heal_count, "heal_failed": True,
            })
        else:
            heal_count += 1
            # heal_count를 병렬 상태 파일에 기록 (단일 파이프라인 오염 방지)
            update_state(state_path, lambda fresh: {**fresh, "heal_count": heal_count})
            heal_ctx = build_heal_context(report, heal_count, state_path)
            if heal_ctx:
                # auto_heal 시도 (deterministic 패치)
                auto_heal_applied = _try_auto_heal(state_path=state_path)  # P53: 병렬 상태 경로 전달
                pl = "quick" if quick_mode else "parallel"
                if auto_heal_applied:
                    print("[99] auto_heal 성공 -- Agent 힐링 불필요할 수 있습니다.")
                    print("     python parallel/99_merge.py 를 다시 실행하여 확인하세요.")
                print_heal_instructions(heal_ctx, pipeline=pl)
            else:
                # build_heal_context가 None 반환 (사이트 불가 또는 전체 반복)
                HEAL_CONTEXT_STATE.unlink(missing_ok=True)
    else:
        HEAL_CONTEXT_STATE.unlink(missing_ok=True)

        # 힐링을 거쳐 통과한 경우(heal_count > 0), 패치 전/후 assertion 무결성 확인
        # (06_heal.py/assert_guard.py와 동일한 방식 — 경고만 출력, 파이프라인은 막지 않음)
        if heal_count > 0:
            prior_run_state = read_state(state_path)
            pre_heal = prior_run_state.get("pre_heal_assertions")
            if pre_heal:
                baseline = prior_run_state.get("original_assertions") or pre_heal
                post_files = prior_run_state.get("pre_heal_files") or list(pre_heal.keys())
                post_snap = snapshot_assertions(post_files)
                integrity = compare_assertions(baseline, post_snap)
                integrity["baseline"] = (
                    "최초 생성 기준" if prior_run_state.get("original_assertions") else "직전 패치 기준"
                )
                integrity["heal_round"] = heal_count
                if integrity["has_warnings"]:
                    print()
                    print("=" * 60)
                    print(f"  ⚠️  [assertion 무결성 경고] 힐링 중 assertion이 약화되었을 수 있습니다"
                          f" ({integrity['baseline']}, {heal_count}회차)")
                    print("=" * 60)
                    for w in integrity["warnings"]:
                        print(f"  - {w}")
                    print("=" * 60)
                    print()
                else:
                    print(f"[99] assertion 품질 이상 없음 ({integrity['baseline']}).")
                update_state(state_path, lambda fresh: {**fresh, "assertion_integrity": integrity})

    # 4. HTML 리포트 (힐링 완료 후에만 생성: 전체 통과 또는 최대 힐링 초과)
    is_final_run = (not has_issues) or heal_count >= MAX_HEAL or args.no_heal
    index_path = None
    if is_final_run:
        report_dir = PROJECT_ROOT / "tests" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        index_path = report_dir / f"parallel_index_{ts}.html"
        index_path.write_text(
            build_html(test_results, pytest_summary, now,
                       target_groups=args.group,
                       skip_messages=parse_skip_messages(report)),
            encoding="utf-8"
        )

    # 5. state/parallel.json (또는 quick.json)에 실행 결과 저장
    passed = pytest_summary.get("passed", 0)
    failed = pytest_summary.get("failed", 0) + pytest_summary.get("error", 0)
    skipped = pytest_summary.get("skipped", 0)
    total = passed + failed + skipped
    pass_rate = round(passed / total * 100, 1) if total else 0

    # 그룹별 결과 집계
    group_results = {}
    for nodeid, outcome in test_results.items():
        parts = nodeid.split("/")
        group = None
        for i, p in enumerate(parts):
            if p == "generated" and i + 1 < len(parts):
                group = parts[i + 1]
                break
        if not group:
            continue
        if group not in group_results:
            group_results[group] = {"passed": 0, "failed": 0, "skipped": 0, "tests": []}
        if outcome == "passed":
            group_results[group]["passed"] += 1
        elif outcome == "skipped":
            group_results[group]["skipped"] += 1
        else:
            group_results[group]["failed"] += 1
        group_results[group]["tests"].append({
            "nodeid": nodeid,
            "name": nodeid.split("::")[-1] if "::" in nodeid else nodeid,
            "passed": outcome == "passed",
            "outcome": outcome,
        })

    _new_execution_result = {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "total": total,
        "pass_rate": pass_rate,
        "report_path": str(index_path.relative_to(PROJECT_ROOT)) if index_path else None,
        "report_name": index_path.name if index_path else None,
        "group_results": group_results,
        "executed_at": now,
        "heal_count": heal_count,
    }
    if failed == 0:
        _new_status = ParallelStatus.DONE
    elif args.no_heal:
        _new_status = ParallelStatus.DONE
    elif heal_count >= MAX_HEAL:
        _new_status = ParallelStatus.HEAL_FAILED
    else:
        _new_status = ParallelStatus.HEAL_NEEDED

    # pytest 실행(전체 그룹, 수 분~수십 분 소요 가능)이 끝난 시점의 최신 상태
    # 위에 이번 실행이 책임지는 필드만 병합해 쓴다 — read_state 시점의 오래된
    # 스냅샷으로 다른 프로세스(대시보드 등)의 갱신을 덮어쓰지 않기 위함.
    update_state(state_path, lambda fresh: {
        **fresh,
        "groups": args.group or [],
        "execution_result": _new_execution_result,
        "status": _new_status,
    })

    # 실행 이력 기록
    _duration = round(_time.monotonic() - _start_time, 1)
    groups_list = list(group_results.keys()) if group_results else (args.group or [])
    append_run_history({
        "timestamp": now,
        "pipeline": "quick" if quick_mode else "parallel",
        "groups": groups_list,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "total": total,
        "pass_rate": pass_rate,
        "heal_count": heal_count,
        "first_pass": failed == 0 and heal_count == 0,
        "duration_sec": _duration,
    })

    # 6. 요약 출력
    print()
    print("=" * 60)
    print("  QA Report Generated")
    print("=" * 60)
    print(f"  Total   : {total}")
    print(f"  Passed  : {passed}")
    print(f"  Failed  : {failed}")
    if skipped:
        print(f"  Skipped : {skipped}")
    print()
    print(f"  Tests  : {GENERATED_DIR}")
    print(f"  Report : {index_path or '(힐링 필요 — 실패 수정 후 재실행 시 생성)'}")
    print("=" * 60)
    slog("step_end", step="99_merge", passed=passed, failed=failed,
         total=total, pass_rate=pass_rate, heal_count=heal_count,
         duration_sec=_duration)


if __name__ == "__main__":
    main()
