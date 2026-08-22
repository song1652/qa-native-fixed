"""
Step 6-auto -- 자동 힐링 (deterministic pattern fixes)
LLM 없음. 알려진 패턴을 regex 기반으로 자동 패치.
06_heal.py 이후, Agent 호출 전에 실행.

종료코드:
  0 = 모든 실패 자동 수�� 완료 (Agent 불필요)
  1 = 일부 실패 남음 (Agent 힐링 필요)
"""
import json
import re
import subprocess
import sys
from pathlib import Path
from _paths import PIPELINE_STATE, PROJECT_ROOT, read_state, write_state
from _python import PYTHON_EXE

HEAL_STATS_PATH = PROJECT_ROOT / "state" / "heal_stats.json"


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
    for old_val, new_val in [("timeout=5000", "timeout=15000"),
                              ("timeout=10000", "timeout=20000")]:
        if old_val in source:
            source = source.replace(old_val, new_val)
            changed = True
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

    # import re 추가 (없으면)
    if "re.compile" in new_source and "import re" not in new_source:
        new_source = "import re\n" + new_source

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


def main():
    state_path = PIPELINE_STATE
    if not state_path.exists():
        print("[오류] state/pipeline.json 없음.")
        sys.exit(1)

    state = read_state(state_path)
    heal_context = state.get("heal_context")

    if not heal_context or state.get("step") != "heal_needed":
        print("[스킵] heal_needed 상태가 아님.")
        sys.exit(0)

    failures = heal_context.get("failures", [])
    if not failures:
        print("[06-auto] 실패 없음.")
        sys.exit(0)

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

    # 패치된 파일 저장
    for fpath, source in patched_files.items():
        Path(fpath).write_text(source, encoding="utf-8")

    print(f"\n[06-auto] {len(patched_files)}개 파일, {patch_count}건 자동 패치 완료")

    # 패치된 파일만 재��행
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

        # 결과 파싱 (stdout 카운트 방식 유지 + 크래시 감지 보강)
        passed = result.stdout.count(" PASSED")
        failed = result.stdout.count(" FAILED")

        # pytest가 크래시(수집 실패, import 오류 등)하면 passed=0, failed=0이 되지만
        # returncode != 0이므로 이를 실패로 처리 (성공 오판 방지)
        if result.returncode != 0 and passed == 0 and failed == 0:
            print(f"[06-auto] pytest 크래시 (exit {result.returncode}) — Agent 힐링 필요")
            if result.stderr:
                print(result.stderr[:300])
            sys.exit(1)

        print(f"[06-auto] 재실행 결과: {passed} passed, {failed} failed")

        if failed == 0:
            # 모든 자동 패치 성공 -- 남은 실패에서 패치된 것 제거
            patched_ids = {nid for nid in patched_nodeids}
            remaining = [f for f in failures if f.get("test_id") not in patched_ids]

            if not remaining:
                print("[06-auto] 모든 실패 자동 수정 완료!")
                # heal_context 업데이트
                heal_context["failures"] = []
                heal_context["failure_count"] = 0
                heal_context["auto_healed"] = len(patched_nodeids)
                state["heal_context"] = heal_context
                write_state(state_path, state)

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
                heal_context["failures"] = remaining
                heal_context["failure_count"] = len(remaining)
                heal_context["auto_healed"] = len(patched_nodeids) - failed
                state["heal_context"] = heal_context
                write_state(state_path, state)
                sys.exit(1)
        else:
            print(f"[06-auto] 자동 패치 후에도 {failed}건 실패 -- Agent 힐링 필요")
            sys.exit(1)

    sys.exit(1)


if __name__ == "__main__":
    main()
