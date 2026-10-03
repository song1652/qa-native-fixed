"""
Step 6-auto -- 자동 힐링 (deterministic pattern fixes)
LLM 없음. 알려진 패턴을 regex 기반으로 자동 패치.
06_heal.py 이후, Agent 호출 전에 실행.

종료코드:
  0 = 모든 실패 자동 수정 완료 (Agent 불필요)
  1 = 일부 실패 남음 (Agent 힐링 필요)
  3 = 스킵 (heal_needed 상태가 아님 / 실패 없음) — 단일·병렬 공통
  5 = 자동 복구 중단 (새 DOM 수집/검증 실패, 원본 복원)
"""
import ast
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from _paths import PIPELINE_STATE, read_state, HEAL_STATS_PATH
from _pipeline_registry import Step
from _python import PYTHON_EXE
from heal_utils import refresh_heal_snapshot, load_heal_execution_state
from heal_utils import update_heal_state as update_state
from error_policy import classify_error as recovery_for_error, recovery_for_result

EXIT_RECOVERY_STOPPED = 5
_refresh_heal_snapshot = refresh_heal_snapshot


def _insert_import(source: str, import_line: str) -> str:
    """모듈 docstring / __future__ import 뒤에 import 문을 삽입.

    `from __future__ import annotations` 는 반드시 파일 최상단(docstring 제외)에
    와야 하므로 무조건 앞에 붙이면 SyntaxError가 난다.
    """
    lines = source.splitlines(keepends=True)

    insert_at = 0
    try:
        tree = ast.parse(source)
    except SyntaxError:
        tree = None

    if tree is not None:
        for node in tree.body:
            is_docstring = (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            )
            is_future = (
                isinstance(node, ast.ImportFrom) and node.module == "__future__"
            )
            if is_docstring or is_future:
                insert_at = node.end_lineno  # 1-based 끝줄 → 그 다음 줄 인덱스
            else:
                break
    else:
        # 파싱 실패 시 최소한 __future__ 라인만이라도 건너뛴다
        for i, line in enumerate(lines):
            if line.startswith("from __future__ import"):
                insert_at = i + 1

    lines.insert(insert_at, import_line)
    return "".join(lines)


# ── 자동 패치 함수들 ─────────────────────────────────────────────


def fix_strict_mode(source: str, traceback: str) -> tuple[str, bool]:
    """strict mode violation → .first 추가."""
    if "strict mode violation" not in traceback.lower():
        return source, False

    # traceback에서 문제 locator 라인 추출
    match = re.search(r'locator\("([^"]+)"\)', traceback)
    if not match:
        return source, False

    selector = match.group(1)
    # 소스에서 해당 셀렉터를 사용하는 곳에 .first가 없으면 추가
    pattern = re.compile(
        rf'(page\.locator\("{re.escape(selector)}"\))(?!\.first)'
    )
    new_source, count = pattern.subn(r'\1.first', source)
    return new_source, count > 0


def fix_timeout_increase(source: str, traceback: str) -> tuple[str, bool]:
    """Timeout 오류 → timeout 값 증가."""
    if "timeout" not in traceback.lower():
        return source, False

    changed = False
    # timeout=5000 → 15000, timeout=10000 → 20000
    # 주의: traceback에 "timeout"이 있으면 파일 내 모든 timeout을 올린다.
    # 실패 지점 특정이 어려워 범위를 좁히지 못하므로, 대신 치환 내역을 로그로 남긴다.
    for old_val, new_val in [("timeout=5000", "timeout=15000"),
                              ("timeout=10000", "timeout=20000")]:
        count = source.count(old_val)
        if count:
            source = source.replace(old_val, new_val)
            changed = True
            print(f"    [timeout] {old_val} → {new_val} ({count}곳)")
    return source, changed


def fix_to_have_class_regex(source: str, traceback: str) -> tuple[str, bool]:
    """to_have_class(r"...") → to_have_class(re.compile(r"..."))."""
    pattern = re.compile(r'to_have_class\(r"(.*?)",')
    if not pattern.search(source):
        return source, False

    new_source = pattern.sub(r'to_have_class(re.compile(r"\1"),', source)
    # not_to_have_class도 처리
    pattern2 = re.compile(r'not_to_have_class\(r"(.*?)",')
    new_source = pattern2.sub(r'not_to_have_class(re.compile(r"\1"),', new_source)

    # import re 추가 (없으면) — __future__ import 앞에 오면 SyntaxError
    if "re.compile" in new_source and "import re" not in new_source:
        new_source = _insert_import(new_source, "import re\n")

    return new_source, new_source != source


def fix_triple_click(source: str, traceback: str) -> tuple[str, bool]:
    """triple_click() → click(click_count=3)."""
    if "triple_click" not in source and "triple_click" not in traceback:
        return source, False

    new_source = source.replace("triple_click()", "click(click_count=3)")
    return new_source, new_source != source


def fix_evaluate_return(source: str, traceback: str) -> tuple[str, bool]:
    """page.evaluate('return ...') → page.evaluate('() => ...')."""
    if "illegal return" not in traceback.lower() and "syntaxerror" not in traceback.lower():
        return source, False

    # page.evaluate("return X") → page.evaluate("() => X")
    # 큰따옴표/작은따옴표 각각 처리 (중첩 따옴표 안전)
    pattern_dq = re.compile(r'page\.evaluate\(\s*"return\s+([^"]+)"\s*\)')
    new_source = pattern_dq.sub(r'page.evaluate("() => \1")', source)
    pattern_sq = re.compile(r"page\.evaluate\(\s*'return\s+([^']+)'\s*\)")
    new_source = pattern_sq.sub(r"page.evaluate('() => \1')", new_source)
    return new_source, new_source != source


def fix_unicode_encoding(source: str, traceback: str) -> tuple[str, bool]:
    """UnicodeDecodeError cp949 → open() 에 encoding='utf-8' 추가."""
    if "unicodedecodeerror" not in traceback.lower() and "cp949" not in traceback.lower():
        return source, False

    new_source = re.sub(
        r"open\(([^)]+),\s*['\"]r['\"]\s*\)",
        lambda m: m.group(0)[:-1] + ", encoding='utf-8')",
        source
    )
    return new_source, new_source != source


def fix_modal_timeout(source: str, traceback: str) -> tuple[str, bool]:
    """모달 wait_for timeout 부족 → 20000으로 증가."""
    if "timeout" not in traceback.lower():
        return source, False
    if "modal" not in source and "modal" not in traceback.lower():
        return source, False

    new_source = source.replace(
        ".wait_for(state='visible', timeout=10000)",
        ".wait_for(state='visible', timeout=20000)"
    )
    return new_source, new_source != source


def _load_frequent_patterns(min_count: int = 3) -> list[dict]:
    """heal_stats.json에서 빈출 패턴(count >= min_count) 로드."""
    if not HEAL_STATS_PATH.exists():
        return []
    try:
        stats = json.loads(HEAL_STATS_PATH.read_text(encoding="utf-8"))
        patterns = stats.get("patterns", {})
        frequent = [
            v for v in patterns.values()
            if v.get("count", 0) >= min_count
            and v.get("summary", "") != "unknown"
            and "legacy" not in v.get("summary", "")
        ]
        return sorted(frequent, key=lambda x: x["count"], reverse=True)
    except Exception:
        return []


# 모든 패치 함수 목록 (정적 + 빈출 패턴 기반)
PATCHERS = [
    fix_strict_mode,
    fix_timeout_increase,
    fix_to_have_class_regex,
    fix_triple_click,
    fix_evaluate_return,
    fix_unicode_encoding,
    fix_modal_timeout,
]


# ── 메인 ─────────────────────────────────────────────────────────


def _atomic_write_text(target: Path, content: str, encoding: str = "utf-8") -> None:
    """tempfile + os.replace로 원자적 쓰기 (#28).

    예전엔 target.write_text(content)로 바로 truncate-write했다. 쓰는
    도중 프로세스가 죽으면(kill, OOM) 대상 파일이 절반만 쓰인 채로
    남을 수 있다 — 예전엔 패치 전 원본을 백업해뒀지만(f9fe4ec에서 죽은
    코드로 제거됨) 지금은 복구 수단이 아예 없다. 임시 파일을 target과
    같은 디렉터리(같은 파일시스템)에 만들어야 replace()가 원자적임이
    보장된다.
    """
    fd, tmp_path = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with open(fd, "w", encoding=encoding) as f:
            f.write(content)
        Path(tmp_path).replace(target)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def _make_heal_context_mutator(failures_left: list, auto_healed: int):
    """자동 힐링 결과 필드만 최신 상태 위에 덮어쓰는 mutator를 만든다.

    state를 읽은 뒤 pytest 재실행(최대 300초) + assert_guard까지 시간이 크게
    벌어지므로, 그 사이 다른 프로세스가 쓴 값을 통째로 덮어쓰지 않도록
    read+write 대신 update_state(RMW)를 쓴다. heal_context 자체도 fresh 기준으로
    병합해 다른 프로세스가 추가한 키를 잃지 않게 한다.
    """
    def _mutator(fresh: dict) -> dict:
        ctx = {
            **fresh.get("heal_context", {}),
            "failures": failures_left,
            "failure_count": len(failures_left),
            "auto_healed": auto_healed,
        }
        return {**fresh, "heal_context": ctx}

    return _mutator


def _rerun_outcome(stdout: str, returncode: int, expected_count: int) -> dict:
    """패치 재실행 pytest stdout을 해석해 전부 통과했는지 판정한다.

    pytest는 수집/픽스처 오류를 FAILED가 아니라 ERROR로 출력한다. 예전에는
    `failed == 0`을 성공 기준으로 썼는데, 이러면 "2 PASSED / 1 ERROR"처럼
    ERROR가 섞여도 failed=0이라 성공으로 오판했다(#24). 그래서 "전부 성공"은
    반드시 실제로 통과한 개수(passed)가 기대 개수(expected_count)와
    같은지로 판정한다.
    """
    passed = stdout.count(" PASSED")
    failed = stdout.count(" FAILED")
    errors = stdout.count(" ERROR")
    # 크래시(수집 실패, import 오류 등)면 passed=0, failed=0인데 returncode != 0.
    crashed = returncode != 0 and passed == 0 and failed == 0
    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "crashed": crashed,
        "all_passed": returncode == 0 and passed == expected_count and failed == 0 and errors == 0,
    }


def _main():
    import argparse
    from _paths import PARALLEL_STATE, QUICK_STATE
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--state-path",
        default=None,
        help=(
            "상태 JSON 경로 (기본: state/pipeline.json). "
            "병렬 파이프라인에서는 state/parallel.json을 지정 (P53)."
        ),
    )
    parser.add_argument(
        "--state-key",
        default=None,
        help="상태 파일의 heal_needed 판정 키 (기본: step; parallel은 status).",
    )
    parser.add_argument(
        "--heal-context-path",
        default=None,
        help=(
            "heal_context를 읽어올 JSON 파일 경로 (P65). "
            "지정 시 state 파일의 heal_context를 무시하고 이 파일을 사용한다. "
            "병렬 파이프라인에서 heal_context.json을 별도 저장하는 경우에 사용."
        ),
    )
    args, _ = parser.parse_known_args()

    # state-path / state-key 결정
    if args.state_path:
        state_path = Path(args.state_path)
        state_key = args.state_key or ("status" if state_path in (PARALLEL_STATE, QUICK_STATE) else "step")
    else:
        state_path = PIPELINE_STATE
        state_key = "step"

    if not state_path.exists():
        print(f"[오류] {state_path.name} 없음.")
        sys.exit(1)

    try:
        state = load_heal_execution_state(read_state(state_path), state_path=state_path)
    except RuntimeError as exc:
        print(f"[06-auto] {exc}")
        sys.exit(EXIT_RECOVERY_STOPPED)

    # P65: --heal-context-path가 지정된 경우 외부 파일에서 heal_context 로드.
    # 병렬 파이프라인은 heal_context를 state와 별도 파일(heal_context.json)에 저장하므로
    # state.get("heal_context")가 항상 None → 스킵되는 dead path를 방지한다.
    if args.heal_context_path:
        hc_path = Path(args.heal_context_path)
        if not hc_path.exists():
            print(f"[오류] --heal-context-path 파일 없음: {hc_path}")
            sys.exit(1)
        import json as _json
        heal_context = _json.loads(hc_path.read_text(encoding="utf-8"))
        # 외부 heal_context를 사용할 때는 상태 파일의 status 검사를 건너뜀.
        # (99_merge.py가 이미 heal_needed 상태임을 확인한 뒤 호출하기 때문)
    else:
        heal_context = state.get("heal_context")
        # L-1(P111): state_key="step"(단일) → Step.HEAL_NEEDED, state_key="status"(병렬) → ParallelStatus.HEAL_NEEDED.
        # 두 상수의 값("heal_needed")이 동일하므로 Step을 기준으로 비교해도 동작이 동등하다.
        if not heal_context or state.get(state_key) != Step.HEAL_NEEDED:  # m1(P93) + L-1(P111)
            print("[스킵] heal_needed 상태가 아님.")
            sys.exit(3)  # 스킵 코드 — 호출자가 "자동 완료"와 구분할 수 있어야 함

    if os.environ.get("QA_RUN_ID") and heal_context.get("run_id") != state.get("execution_result", {}).get("run_id"):
        print("[06-auto] 다른 실행의 힐링 컨텍스트 — 자동 복구 중단")
        sys.exit(EXIT_RECOVERY_STOPPED)

    failures = heal_context.get("failures", [])
    if not failures:
        print("[06-auto] 실패 없음.")
        sys.exit(3)  # 스킵 코드 — 호출자가 "자동 완료"와 구분할 수 있어야 함

    originals = {}
    written_files = set()

    def stop_recovery(reason):
        stopped = {**heal_context, "recovery_stopped": True,
                   "auto_heal_rerun_error": reason, "auto_healed": 0,
                   "error": f"자동 복구 중단: {reason}"}
        if args.heal_context_path:
            _atomic_write_text(hc_path, json.dumps(stopped, ensure_ascii=False, indent=2))
        def mark(fresh):
            updated = {**fresh, "heal_context": stopped}
            updated.pop("heal_subagent_contexts", None)
            if state_key == "step":
                updated["step"] = Step.HEAL_FAILED
            return updated
        update_state(state_path, mark)
        print(f"[06-auto] {stopped['error']} — 추가 실행 없이 원본 복원")
        sys.exit(EXIT_RECOVERY_STOPPED)

    if heal_context.get("recovery_stopped"):
        stop_recovery("이전 복구가 중단되었습니다")
    execution = state.get("execution_result", {})
    if execution:
        admission = recovery_for_result({**execution, "errors": execution.get("errors") or [
            {"error": failure.get("traceback", "")} for failure in failures
        ]})
        if not admission["can_heal"]:
            heal_context = {**heal_context, "recovery": admission}
            stop_recovery(admission["message"])
    for failure in failures:
        recovery = recovery_for_error(failure.get("traceback", ""))
        if not recovery["can_heal"]:
            heal_context = {**heal_context, "recovery": recovery}
            stop_recovery(recovery["message"])
    try:
        fresh_dom = _refresh_heal_snapshot(heal_context, state)
        if not fresh_dom:
            raise RuntimeError("새 DOM 없음")
    except Exception as exc:
        stop_recovery(f"새 DOM 수집 실패: {exc}")
    heal_context = {**heal_context, "fresh_dom_info": fresh_dom}
    if args.heal_context_path:
        _atomic_write_text(hc_path, json.dumps(heal_context, ensure_ascii=False, indent=2))
    else:
        update_state(state_path, lambda fresh: {**fresh, "heal_context": {**fresh.get("heal_context", {}), "fresh_dom_info": fresh_dom}})

    # 빈출 패턴 보고 (Agent 힌트)
    frequent = _load_frequent_patterns(min_count=3)
    if frequent:
        print(f"[06-auto] 빈출 패턴 Top {min(len(frequent), 5)}:")
        for p in frequent[:5]:
            print(f"  [{p['count']}회] {p['error_type']}: {p['summary'][:60]}")
        print()

    # 실패 파일별 패치 적용
    patched_files = {}
    patch_count = 0

    for f in failures:
        test_id = f.get("test_id", "")
        tb = f.get("traceback", "")

        if "::" not in test_id:
            continue

        file_path = Path(test_id.split("::")[0])
        if not file_path.exists():
            continue

        # 이미 패치한 파일은 재사용
        fkey = str(file_path)
        if fkey in patched_files:
            source = patched_files[fkey]
        else:
            originals[file_path] = file_path.read_bytes()
            source = originals[file_path].decode("utf-8")

        original = source
        applied = []

        for patcher in PATCHERS:
            source, fixed = patcher(source, tb)
            if fixed:
                applied.append(patcher.__name__)

        if source != original:
            patched_files[fkey] = source
            patch_count += len(applied)
            print(f"  [auto] {file_path.name}: {', '.join(applied)}")

    if not patched_files:
        print("[06-auto] 자동 패치 가능한 패턴 없음.")
        sys.exit(1)

    # Each changed file gets one verification; the first failure ends this transaction.
    verified_ids = set()
    verification_complete = False
    try:
        for fpath, source in list(patched_files.items()):
            target = Path(fpath)
            try:
                compile(source, fpath, "exec")
            except SyntaxError as exc:
                print(f"[06-auto] {target.name}: 문법 오류 — 패치 취소 ({exc})")
                continue
            nodeids = list(dict.fromkeys(
                f["test_id"] for f in failures
                if f.get("test_id", "").split("::")[0] == fpath
            ))
            try:
                load_heal_execution_state(read_state(state_path), state_path=state_path)
                written_files.add(target)
                _atomic_write_text(target, source)
                verification_id = uuid.uuid4().hex
                verification_owner = (state.get("execution_result", {}).get("run_id")
                                      or heal_context.get("run_id")
                                      or f"autoheal_{uuid.uuid4().hex}")
                result = subprocess.run(
                    [PYTHON_EXE, "-m", "pytest", *nodeids,
                     "-v", "--tb=line", "--no-header", "--maxfail=1", "-p", "no:rerunfailures"],
                    env={**os.environ, "QA_RUN_ID": verification_owner,
                         "QA_INVOCATION_ID": verification_id,
                         "QA_ARTIFACT_PREFIX": f"{verification_owner}__{verification_id}__"},
                    capture_output=True, text=True, timeout=300,
                )
            except Exception as exc:
                heal_context = {**heal_context, "recovery": recovery_for_error(exc)}
                stop_recovery(f"검증 실행 실패: {exc}")
            try:
                load_heal_execution_state(read_state(state_path), state_path=state_path)
            except RuntimeError as exc:
                stop_recovery(str(exc))
            outcome = _rerun_outcome(result.stdout, result.returncode, len(nodeids))
            if not outcome["all_passed"]:
                heal_context = {**heal_context, "recovery": recovery_for_error(result.stdout + result.stderr)}
                stop_recovery(f"복구 검증 실패 (exit {result.returncode})")
            verified_ids.update(nodeids)
        verification_complete = True
    finally:
        if not verification_complete:
            for changed in written_files:
                changed.write_bytes(originals[changed])

    if not verified_ids:
        print("[06-auto] 유효한 자동 패치 없음.")
        sys.exit(1)
    remaining = [f for f in failures if f.get("test_id") not in verified_ids]
    if args.heal_context_path:
        updated = {**heal_context, "failures": remaining, "failure_count": len(remaining),
                   "auto_healed": len(verified_ids)}
        _atomic_write_text(hc_path, json.dumps(updated, ensure_ascii=False, indent=2))
    else:
        update_state(state_path, _make_heal_context_mutator(remaining, len(verified_ids)))
    if not remaining:
        guard = subprocess.run(
            [PYTHON_EXE, str(Path(__file__).parent / "assert_guard.py"), "--state-path", str(state_path)],
            capture_output=True, text=True,
        )
        if guard.stdout:
            print(guard.stdout.rstrip())
    print(f"[06-auto] 검증 통과 {len(verified_ids)}건, 잔여 실패 {len(remaining)}건")
    sys.exit(1 if remaining else 0)


def main():
    previous = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(128 + signum))
    try:
        _main()
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    main()
