"""
Step 6-auto -- 자동 힐링 (deterministic pattern fixes)
LLM 없음. 알려진 패턴을 regex 기반으로 자동 패치.
06_heal.py 이후, Agent 호출 전에 실행.

종료코드:
  0 = 모든 실패 자동 수정 완료 (Agent 불필요)
  1 = 일부 실패 남음 (Agent 힐링 필요)
  3 = 스킵 (heal_needed 상태가 아님 / 실패 없음) — 단일·병렬 공통
"""
import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from _paths import PIPELINE_STATE, PROJECT_ROOT, read_state, update_state, HEAL_STATS_PATH
from _pipeline_registry import ParallelStatus  # m1(P93): 문자열 하드코딩 제거
from _python import PYTHON_EXE


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
        "all_passed": passed == expected_count,
    }


def main():
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

    state = read_state(state_path)

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
        if not heal_context or state.get(state_key) != ParallelStatus.HEAL_NEEDED:  # m1(P93)
            print("[스킵] heal_needed 상태가 아님.")
            sys.exit(3)  # 스킵 코드 — 호출자가 "자동 완료"와 구분할 수 있어야 함

    failures = heal_context.get("failures", [])
    if not failures:
        print("[06-auto] 실패 없음.")
        sys.exit(3)  # 스킵 코드 — 호출자가 "자동 완료"와 구분할 수 있어야 함

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
            source = file_path.read_text(encoding="utf-8")

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

    # 패치된 파일 저장 (문법 검증을 통과한 것만 기록)
    # 검증이 쓰기보다 앞서므로 원본이 훼손될 구간이 없다 → 별도 백업/복원 불필요.
    for fpath, source in list(patched_files.items()):
        target = Path(fpath)
        try:
            # ast.parse가 아닌 compile: ast.parse는 __future__ import 위치 규칙을
            # 검사하지 않아 바로 이 버그를 놓친다.
            compile(source, fpath, "exec")
        except SyntaxError as e:
            print(f"  [오류] {target.name}: 패치 결과가 문법 오류 — 패치 취소 "
                  f"(line {e.lineno}: {e.msg})")
            del patched_files[fpath]
            continue

        _atomic_write_text(target, source)

    if not patched_files:
        print("[06-auto] 유효한 자동 패치 없음 (전부 문법 오류로 취소).")
        sys.exit(1)

    print(f"\n[06-auto] {len(patched_files)}개 파일, {patch_count}건 자동 패치 완료")

    # 패치된 파일만 재실행
    patched_nodeids = []
    for f in failures:
        test_id = f.get("test_id", "")
        if "::" in test_id and test_id.split("::")[0] in patched_files:
            patched_nodeids.append(test_id)

    if patched_nodeids:
        print(f"[06-auto] {len(patched_nodeids)}개 테스트 재실행 중...")
        try:
            result = subprocess.run(
                [PYTHON_EXE, "-m", "pytest"] + patched_nodeids +
                ["-v", "--tb=line", "--no-header"],
                capture_output=True, text=True, timeout=300,
            )
        except subprocess.TimeoutExpired:
            print("[06-auto] pytest 재실행 타임아웃 (300s) — Agent 힐링 필요")
            sys.exit(1)

        # 결과 파싱 — "전부 성공"은 passed == 기대 개수로 판정 (#24: ERROR가
        # 섞이면 failed==0이라도 실패다. _rerun_outcome 참조)
        outcome = _rerun_outcome(result.stdout, result.returncode, len(patched_nodeids))
        passed, failed, errors = outcome["passed"], outcome["failed"], outcome["errors"]

        if outcome["crashed"]:
            print(f"[06-auto] pytest 크래시 (exit {result.returncode}) — Agent 힐링 필요")
            if result.stderr:
                print(result.stderr[:300])
            sys.exit(1)

        print(f"[06-auto] 재실행 결과: {passed} passed, {failed} failed, {errors} error")

        if outcome["all_passed"]:
            # 모든 자동 패치 성공 -- 남은 실패에서 패치된 것 제거
            patched_ids = {nid for nid in patched_nodeids}
            remaining = [f for f in failures if f.get("test_id") not in patched_ids]

            if not remaining:
                print("[06-auto] 모든 실패 자동 수정 완료!")
                # heal_context 업데이트 (RMW — 재실행 사이의 변경을 덮어쓰지 않음)
                update_state(
                    state_path,
                    _make_heal_context_mutator([], len(patched_nodeids)),
                )
                # H-2(P105): --heal-context-path 지정 시 해당 파일에도 동기화
                # (06_auto_heal은 그 파일에서 읽지만 update_state는 state_path에만 씀 → 불일치 해소)
                if args.heal_context_path:
                    _hc_updated = {**heal_context, "failures": [], "failure_count": 0,
                                   "auto_healed": len(patched_nodeids)}
                    _atomic_write_text(hc_path, json.dumps(_hc_updated, ensure_ascii=False, indent=2))

                # 패치 후 assertion 무결성 검증 (assert_guard.py 자동 호출)
                _scripts_dir = Path(__file__).parent
                _guard = subprocess.run(
                    [PYTHON_EXE, str(_scripts_dir / "assert_guard.py")],
                    capture_output=True, text=True,
                )
                # assert_guard는 advisory — 오류나도 파이프라인을 막지 않음
                if _guard.stdout:
                    print(_guard.stdout.rstrip())
                if _guard.returncode not in (0, 1):
                    print(f"[06-auto] assert_guard 비정상 종료 (exit {_guard.returncode})")

                sys.exit(0)
            else:
                print(f"[06-auto] {len(remaining)}건 잔여 실패 -- Agent 힐링 필요")
                # 이 분기는 failed == 0 -- 재실행한 patched_nodeids는 전부 통과했다.
                # 잔여 실패(remaining)는 애초에 패치 대상이 아니었던 테스트들이라
                # 자동 힐링 건수에서 뺄 것이 없다.
                update_state(
                    state_path,
                    _make_heal_context_mutator(remaining, len(patched_nodeids)),
                )
                # H-2(P105): --heal-context-path 지정 시 해당 파일에도 동기화
                if args.heal_context_path:
                    _hc_updated = {**heal_context, "failures": remaining,
                                   "failure_count": len(remaining), "auto_healed": len(patched_nodeids)}
                    _atomic_write_text(hc_path, json.dumps(_hc_updated, ensure_ascii=False, indent=2))
                sys.exit(1)
        else:
            not_passed = len(patched_nodeids) - passed
            print(f"[06-auto] 자동 패치 후에도 {not_passed}건 미통과(FAILED/ERROR) -- Agent 힐링 필요")
            sys.exit(1)

    sys.exit(1)


if __name__ == "__main__":
    main()
