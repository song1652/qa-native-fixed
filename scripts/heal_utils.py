"""
힐링 공용 유틸리티.

06_heal.py와 99_merge.py에서 공통으로 사용하는 함수들을 모아놓은 모듈.
- classify_error: traceback → 오류 유형 분류
- extract_key_lines: traceback에서 핵심 라인 추출
- append_lessons: lessons_learned.md 자동 기록
- find_screenshot_for_test: 스크린샷 검색
- snapshot_assertions: 테스트 파일 assertion 패턴 스냅샷
- compare_assertions: 패치 전후 assertion 약화 감지
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from _paths import PROJECT_ROOT, update_state

LESSONS_PATH = PROJECT_ROOT / "agents" / "lessons_learned.md"
LESSONS_AUTO_PATH = PROJECT_ROOT / "agents" / "lessons_learned_auto.md"
SCREENSHOTS_DIR = PROJECT_ROOT / "tests" / "screenshots"
HEAL_STATS_PATH = PROJECT_ROOT / "state" / "heal_stats.json"

HEAL_BATCH_SIZE = 6  # 힐링 배치당 실패 테스트 수
MCP_SNAPSHOT_ERROR_TYPES = frozenset({"Locator", "Assertion", "Timeout"})

# 정확한 값을 검증하는 playwright expect 메서드 (정밀 assertion)
STRICT_METHODS = frozenset({
    "to_have_text", "to_have_value", "to_have_url", "to_have_count",
    "to_have_class", "to_have_attribute", "to_have_title",
})
# 존재/상태만 확인하는 playwright expect 메서드 (느슨한 assertion)
WEAK_METHODS = frozenset({
    "to_be_visible", "to_be_attached", "to_be_enabled", "to_be_checked",
})


def classify_error(traceback: str) -> str:
    """traceback에서 오류 유형 분류.

    분류 우선순위: Timeout > Locator > Assertion > URL > JS평가
                  > Python런타임 > Playwright일반 > 기타

    NOTE: Timeout을 Locator보다 먼저 검사해야 함.
    Playwright 타임아웃 traceback에는 항상 "waiting for locator"가 포함되어
    Locator 키워드가 먼저 매칭되면 모든 Timeout이 Locator로 오분류됨.
    """
    tb = traceback.lower()

    # 1. Timeout 오류 (Locator보다 먼저 — "waiting for locator" 포함 때문)
    # Playwright timeout 패턴: "TimeoutError", "Timeout 30000ms exceeded", "timed out" 등
    if any(k in tb for k in ["timeouterror", "timed out", "timeout exceeded",
                              "ms exceeded", "page timeout", "navigation timeout"]):
        return "Timeout"
    # "timeout" 단독 키워드는 locator/assertion 미포함 시에만
    # "locator"가 포함된 경우 Locator 우선 → 2번 블록에서 처리
    if "timeout" in tb and not any(k in tb for k in [
        "strict mode violation", "element not found",
        "no element", "getby", "waiting for selector", "locator",
    ]):
        return "Timeout"

    # 2. Locator 오류 (셀렉터/요소 관련)
    if any(k in tb for k in [
        "strict mode violation", "element not found", "locator",
        "no element", "getby", "waiting for selector",
        "not visible", "not attached", "intercepted",
        "element is not", "detached from", "frame was detached",
    ]):
        return "Locator"

    # 3. Assertion 오류 (기대값 불일치)
    if any(k in tb for k in [
        "expected", "to contain", "assertionerror", "to have text",
        "to have url", "to be visible", "to have count", "to have class",
        "assert ", "not equal", "mismatch",
    ]):
        return "Assertion"

    # 4. (구) Timeout 폴백 — 위에서 안 잡힌 경우
    if any(k in tb for k in ["timeout", "timed out"]):
        return "Timeout"

    # 4. URL/Navigation 오류
    if any(k in tb for k in [
        "goto", "navigation", "net::err_", "name_not_resolved",
        "connection refused", "page.goto",
    ]):
        return "URL"

    # 5. JS evaluate 오류
    if any(k in tb for k in [
        "syntaxerror", "referenceerror", "typeerror: cannot read",
        "page.evaluate", "illegal return",
    ]):
        return "JS평가"

    # 6. Python 런타임 오류 (KeyError, ImportError 등)
    if any(k in tb for k in [
        "keyerror", "importerror", "modulenotfounderror", "nameerror",
        "attributeerror", "indexerror", "valueerror", "filenotfounderror",
    ]):
        return "Python런타임"

    # 7. Playwright 일반 오류 (raise Error 등)
    if any(k in tb for k in [
        "playwright._impl", "raise error(", "browser has been closed",
        "target page, context or browser has been closed",
        "protocol error", "channel closed",
    ]):
        return "Playwright일반"

    return "기타"


def extract_key_lines(traceback: str) -> list[str]:
    """트레이스백에서 핵심 오류 라인 최대 3개 추출.

    키워드 매칭 실패 시 traceback의 마지막 비공백 줄을 fallback으로 사용.
    """
    lines = traceback.splitlines()
    key = [line.strip() for line in lines
           if any(k in line for k in [
               "Error", "Expected", "assert", "expect", "Locator",
               "raise ", "failed", "FAILED", "KeyError", "TypeError",
               "ValueError", "ImportError", "SyntaxError", "timeout",
               "not visible", "not attached", "strict mode",
           ])]
    if key:
        return key[:3]
    # fallback: traceback의 마지막 비공백 줄 (unknown 방지)
    non_empty = [line.strip() for line in lines if line.strip()]
    if non_empty:
        return [non_empty[-1]]
    return []


def find_screenshot_for_test(test_name: str) -> dict | None:
    """tests/screenshots/ 에서 테스트명에 매칭되는 스크린샷과 메타데이터를 찾는다."""
    if not SCREENSHOTS_DIR.exists():
        return None
    # 그룹 접두사 패턴 우선 검색 (group__test_name.png)
    candidates = list(SCREENSHOTS_DIR.glob(f"*__{test_name}.png"))
    if not candidates:
        # 이전 형식 fallback (test_name.png)
        candidates = list(SCREENSHOTS_DIR.glob(f"{test_name}.png"))
    if not candidates:
        return None
    shot_path = candidates[0]
    result = {"path": str(shot_path)}
    meta_path = shot_path.with_suffix("").with_suffix(".meta.json")
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            result["url"] = meta.get("url")
            result["timestamp"] = meta.get("timestamp")
            if trace_path := meta.get("trace_path"):
                from pathlib import Path as _Path
                if _Path(trace_path).exists():
                    result["trace_path"] = trace_path
            if console_errors := meta.get("console_errors"):
                result["console_errors"] = console_errors
            if network_failures := meta.get("network_failures"):
                result["network_failures"] = network_failures
        except Exception:
            pass
    return result


def append_lessons(failures: list[dict]) -> None:
    """실패 케이스를 lessons_learned_auto.md에 자동 추가 (중복 검사 포함).

    자동 기록은 _auto.md에만 추가. 큐레이션된 lessons_learned.md는 수동 관리.
    중복 검사는 양쪽 파일 모두 대상.
    """
    if not failures:
        return

    target_path = LESSONS_AUTO_PATH
    if not target_path.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            "# Lessons Learned (Auto) -- 자동 기록 힐링 패턴\n\n"
            "> 자동 생성 파일: heal_utils.py의 append_lessons()가 힐링 시 자동 기록.\n\n---\n\n"
            "## Locator 오류\n\n## Assertion 오류\n\n## Timeout 오류\n\n"
            "## URL 오류\n\n## JS평가 오류\n\n## Python런타임 오류\n\n"
            "## Playwright일반 오류\n\n## 기타\n",
            encoding="utf-8",
        )

    auto_content = target_path.read_text(encoding="utf-8")
    # 큐레이션 파일도 중복 검사 대상에 포함
    curated_content = ""
    if LESSONS_PATH.exists():
        curated_content = LESSONS_PATH.read_text(encoding="utf-8")

    # 기존 파일에서 백틱(`) 안의 summary를 정확히 추출하여 set 구성
    existing_summaries: set[str] = set()
    for content in (auto_content, curated_content):
        for m in re.finditer(r'`([^`]+)`', content):
            existing_summaries.add(m.group(1).strip())

    new_entries: dict[str, list[str]] = {}
    seen_summaries: set[str] = set()  # 같은 배치 내 중복 방지
    skipped = 0

    for f in failures:
        error_type = classify_error(f["traceback"])
        key_lines = extract_key_lines(f["traceback"])
        error_summary = key_lines[0] if key_lines else "(traceback 없음)"

        summary_normalized = error_summary.strip()
        # 중복 판정: (1) traceback 없음 (2) 기존 파일에 이미 존재 (3) 같은 배치 내 중복
        if (summary_normalized == "(traceback 없음)"
                or summary_normalized in existing_summaries
                or summary_normalized in seen_summaries):
            skipped += 1
            continue
        seen_summaries.add(summary_normalized)

        fix_hint = {
            "Locator": "dom_info 셀렉터 재확인, #id 우선 사용",
            "Assertion": "실제 페이지 텍스트/상태로 기댓값 수정",
            "Timeout": "expect(..., timeout=10000) 또는 wait_for_selector 추가",
            "URL": "BASE_URL 또는 goto 인자 재확인",
            "JS평가": "page.evaluate() 내 JS 문법 확인, arrow function 래핑",
            "Python런타임": "test_data 키/import/변수명 확인",
            "Playwright일반": "브라우저 상태 확인, 페이지 닫힘/크래시 대응",
        }.get(error_type, "")

        entry = f"- **{error_type}**: `{error_summary}` -- {fix_hint}\n"
        new_entries.setdefault(error_type, []).append(entry)

    if not new_entries:
        if skipped:
            print(f"[heal_utils] lessons_learned_auto.md: {skipped}건 중복 → 추가 없음")
        return

    for section, entries in new_entries.items():
        section_header = f"## {section} 오류" if section != "기타" else "## 기타"
        insert_text = "\n" + "".join(entries)
        pattern = rf"({re.escape(section_header)}[^\n]*\n(?:<!--[^>]*-->\n)?)"
        if re.search(pattern, auto_content):
            auto_content = re.sub(pattern, r"\1" + insert_text, auto_content, count=1)
        else:
            auto_content += f"\n{section_header}\n{insert_text}"

    target_path.write_text(auto_content, encoding="utf-8")
    added = sum(len(v) for v in new_entries.values())
    print(f"[heal_utils] lessons_learned_auto.md 업데이트: "
          f"{added}건 추가, {skipped}건 중복 건너뜀")


def _summarize_failure(f: dict) -> tuple[str, str, str]:
    """실패 1건 → (error_type, summary, pattern_key). 순수 계산 (상태 참조 없음)."""
    error_type = classify_error(f["traceback"])
    key_lines = extract_key_lines(f["traceback"])
    if key_lines:
        summary = key_lines[0].strip()[:120]
    else:
        # traceback 자체의 마지막 줄을 fallback으로 사용
        tb_lines = [l.strip() for l in f["traceback"].splitlines() if l.strip()]
        summary = tb_lines[-1][:120] if tb_lines else f"no_traceback::{f.get('test_name', 'unknown')}"
    return error_type, summary, f"{error_type}::{summary}"


def update_heal_stats(failures: list[dict]) -> None:
    """heal_stats.json에 오류 패턴별 빈도를 업데이트한다.

    병렬 파이프라인에서 여러 그룹이 동시에 호출하므로 read+write로 갱신하면
    마지막 쓰기가 다른 그룹의 카운트를 덮어써 유실된다. 락 기반 원자적 RMW인
    update_state()로 증가시킨다.
    """
    if not failures:
        return

    # 순수 계산은 락 밖에서 미리 끝내 락 보유 시간을 줄인다.
    computed = [_summarize_failure(f) for f in failures]

    def _mutator(fresh: dict) -> dict:
        # 파일이 없거나 비어 있으면 초기 구조로 시작 (기존 동작과 동일)
        base = fresh if fresh else {"version": 1, "patterns": {}}
        patterns = dict(base.get("patterns") or {})
        for error_type, summary, pattern_key in computed:
            now = datetime.now().isoformat()
            entry = patterns.get(pattern_key)
            if entry:
                patterns[pattern_key] = {
                    **entry,
                    "count": entry.get("count", 0) + 1,
                    "last_seen": now,
                }
            else:
                patterns[pattern_key] = {
                    "count": 1,
                    "error_type": error_type,
                    "summary": summary,
                    "first_seen": now,
                    "last_seen": now,
                }
        return {**base, "patterns": patterns}

    try:
        update_state(HEAL_STATS_PATH, _mutator)
        print(f"[heal_utils] heal_stats.json 업데이트: {len(failures)}건 기록")
    except Exception as e:
        # advisory — 통계 갱신 실패가 파이프라인을 막아서는 안 된다
        print(f"[heal_utils] heal_stats.json 업데이트 실패 (무시): {e}")


def snapshot_assertions(file_paths: list[str]) -> dict:
    """테스트 파일들의 assertion 패턴을 스냅샷으로 추출.

    힐링 패치 전에 호출해 pre_heal_assertions로 저장.
    패치 후 compare_assertions()로 약화 여부 감지.
    """
    snapshot: dict = {}
    pw_pattern = re.compile(r'expect\s*\(.+?\)\s*\.\s*(to_\w+)\s*\(([^)]*)\)')
    assert_pattern = re.compile(r'^\s+assert\s+(.+)')
    trivial_exprs = {"True", "1 == 1", "1", "not False", "False == False"}

    for fp in file_paths:
        p = Path(fp)
        if not p.exists():
            continue
        try:
            source = p.read_text(encoding="utf-8")
        except Exception:
            continue

        assertions: list[dict] = []
        for lineno, line in enumerate(source.splitlines(), 1):
            for m in pw_pattern.finditer(line):
                assertions.append({
                    "line": lineno,
                    "type": "playwright",
                    "method": m.group(1),
                    "arg": m.group(2).strip(),
                    "raw": line.strip(),
                })
            m = assert_pattern.match(line)
            if m:
                expr = m.group(1).strip()
                assertions.append({
                    "line": lineno,
                    "type": "python_assert",
                    "expr": expr,
                    "raw": line.strip(),
                    "trivial": expr in trivial_exprs,
                })

        snapshot[p.name] = {
            "count": len(assertions),
            "playwright_count": sum(1 for a in assertions if a["type"] == "playwright"),
            "python_assert_count": sum(1 for a in assertions if a["type"] == "python_assert"),
            "assertions": assertions,
        }
    return snapshot


def compare_assertions(pre: dict, post: dict) -> dict:
    """패치 전후 assertion 스냅샷 비교 — 약화 패턴 감지.

    약화 패턴:
    1. assertion 수 감소
    2. to_have_text → to_contain_text('') 빈 문자열 매칭
    3. assert True / assert 1 == 1 같은 무의미한 assertion 추가
    """
    warnings: list[str] = []
    details: dict = {}

    for filename, pre_info in pre.items():
        post_info = post.get(filename)
        if not post_info:
            warnings.append(f"{filename}: 파일이 삭제됨")
            continue

        file_warnings: list[str] = []
        pre_count = pre_info["count"]
        post_count = post_info["count"]

        if post_count < pre_count:
            file_warnings.append(
                f"assertion 수 감소: {pre_count} → {post_count} ({pre_count - post_count}개 제거됨)"
            )

        pre_pw = {a["method"] for a in pre_info["assertions"] if a["type"] == "playwright"}
        if "to_have_text" in pre_pw:
            for a in post_info["assertions"]:
                if (a["type"] == "playwright"
                        and a["method"] == "to_contain_text"
                        and a["arg"] in ('', '""', "''")):
                    file_warnings.append("to_have_text → to_contain_text('') 약화 감지 (빈 문자열 매칭)")
                    break

        # 정밀 assertion(STRICT_METHODS)이 줄고, 느슨한 assertion(WEAK_METHODS)은
        # 줄지 않았다면 "정밀 assertion이 느슨한 assertion으로 대체"됐을 가능성
        pre_pw_methods = [a["method"] for a in pre_info["assertions"] if a["type"] == "playwright"]
        post_pw_methods = [a["method"] for a in post_info["assertions"] if a["type"] == "playwright"]
        pre_strict = sum(1 for m in pre_pw_methods if m in STRICT_METHODS)
        post_strict = sum(1 for m in post_pw_methods if m in STRICT_METHODS)
        pre_weak = sum(1 for m in pre_pw_methods if m in WEAK_METHODS)
        post_weak = sum(1 for m in post_pw_methods if m in WEAK_METHODS)
        if post_strict < pre_strict and post_weak >= pre_weak:
            file_warnings.append(
                "정밀 assertion이 느슨한 assertion으로 대체되었을 가능성: "
                f"strict {pre_strict} → {post_strict}, weak {pre_weak} → {post_weak}"
            )

        pre_trivials = {a["expr"] for a in pre_info["assertions"] if a.get("trivial")}
        new_trivials = [
            a["raw"] for a in post_info["assertions"]
            if a.get("trivial") and a["expr"] not in pre_trivials
        ]
        if new_trivials:
            file_warnings.append(f"무의미한 assertion 추가됨: {new_trivials}")

        if file_warnings:
            warnings.extend([f"{filename}: {w}" for w in file_warnings])
            details[filename] = {
                "pre_count": pre_count,
                "post_count": post_count,
                "warnings": file_warnings,
            }

    return {
        "has_warnings": bool(warnings),
        "warnings": warnings,
        "details": details,
        "checked_at": datetime.now().isoformat(),
    }


def build_heal_batches(failures: list[dict], batch_size: int = HEAL_BATCH_SIZE) -> list[list[dict]]:
    """실패 목록을 배치로 분할. 각 배치는 독립적으로 병렬 힐링 가능."""
    if not failures:
        return []
    return [failures[i:i + batch_size] for i in range(0, len(failures), batch_size)]


def print_heal_batches(batches: list[list[dict]], url: str = "",
                       pipeline: str = "single") -> None:
    """배치 분할된 힐링 지시를 HEAL_SUBAGENT_CONTEXTS 형식으로 출력.

    Claude Code가 이 출력을 읽고 Agent tool로 각 배치를 동시 실행한다.
    단일/병렬/빠른 실행 모두 동일한 출력 형식을 사용.
    """
    if not batches:
        return

    total_failures = sum(len(b) for b in batches)
    print()
    print("=" * 60)
    print(f"  [힐링 배치 병렬화] {total_failures}건 실패 → {len(batches)}개 배치")
    print("=" * 60)

    # 각 배치 요약 출력
    for i, batch in enumerate(batches, 1):
        names = [f["test_name"] for f in batch]
        print(f"  배치 {i}/{len(batches)}: {len(batch)}건 -- {', '.join(names[:3])}"
              + (f" 외 {len(names) - 3}개" if len(names) > 3 else ""))

    # lessons_learned 스냅샷
    lessons_text = ""
    for lpath in [LESSONS_PATH, LESSONS_AUTO_PATH]:
        if lpath.exists():
            try:
                lessons_text += lpath.read_text(encoding="utf-8") + "\n"
            except Exception:
                pass

    # JSON 컨텍스트 출력
    contexts = []
    for i, batch in enumerate(batches):
        # 배치 내 파일 경로 수집
        files = set()
        for f in batch:
            tid = f.get("test_id", "")
            if "::" in tid:
                files.add(tid.split("::")[0])

        needs_mcp = any(
            f.get("error_type", classify_error(f.get("traceback", "")))
            in MCP_SNAPSHOT_ERROR_TYPES
            for f in batch
        )
        ctx = {
            "batch_index": i + 1,
            "batch_total": len(batches),
            "pipeline": pipeline,
            "url": url,
            "failure_count": len(batch),
            "failures": batch,
            "files": sorted(files),
            "lessons_learned": lessons_text[-2000:] if lessons_text else "",
            "mcp_snapshot_recommended": needs_mcp,
            "mcp_snapshot_url": url if needs_mcp else "",
        }
        contexts.append(ctx)

    print()
    print("=== HEAL_SUBAGENT_CONTEXTS_START ===")
    print(json.dumps(contexts, ensure_ascii=False, indent=2))
    print("=== HEAL_SUBAGENT_CONTEXTS_END ===")
    print()
    print("=" * 60)
    print(f"  위 HEAL_SUBAGENT_CONTEXTS의 {len(batches)}개 배치를 Agent tool로 동시에 실행해주세요.")
    print(f"  (배치당 최대 {HEAL_BATCH_SIZE}건, 총 {total_failures}건)")
    print()
    print("  각 subagent는:")
    print("  1. 배치 내 실패 파일을 읽고 traceback 분석")
    print("  2. screenshot.trace_path 존재 시: 네트워크 오류·콘솔 에러 의심 케이스에 활용")
    print("     (npx playwright show-trace <파일>.zip — 영상·네트워크·콘솔·DOM 스냅샷 포함)")
    print("  3. lessons_learned 패턴 참조하여 패치")
    print("  4. mcp_snapshot_recommended=true 배치: browser_navigate → browser_snapshot으로")
    print("     실시간 ARIA 트리 확인 후 셀렉터 보정 (Locator/Assertion/Timeout 오류 대상)")
    print("  5. 패치 후 개별 테스트 실행으로 통과 확인")
    print("  6. 패치 후 python scripts/assert_guard.py 실행 — assertion 무결성 검증")
    print("     (assert_guard 경고 시: assert 값이 의도적으로 바뀐 것인지 확인)")
    print("  ※ MCP 실패 시 dom_info 기반 힐링으로 자동 전환 (graceful degradation)")
    print()
    if pipeline == "single":
        print("  완료 후: python scripts/05_execute.py --no-report → python scripts/06_heal.py")
        print("           → python scripts/assert_guard.py (assertion 무결성 확인)")
    else:
        print("  완료 후: python parallel/99_merge.py")
        print("           → python scripts/assert_guard.py (assertion 무결성 확인)")
    print("=" * 60)
