"""
Step 6a -- 힐링 심의 컨텍스트 준비
LLM 없음. 심의 agent에 전달할 컨텍스트를 수집·출력한다.
결과는 state.json에만 저장 (dialog.json은 팀 토론 전용).
모든 파일 읽기를 이 스크립트에서 처리 → agent는 파일 읽기 없이 바로 심의 시작.
"""
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from _paths import PIPELINE_STATE, PROJECT_ROOT, read_state, HEAL_STATS_PATH
from _constants import DEFAULT_GENERATED_FILE


def read_file(path, filter_files=None):
    """파일 또는 디렉토리의 내용을 읽는다.
    filter_files: set of filenames -- 지정 시 해당 파일만 포함 (힐링 시 실패 파일만 전달).
    """
    p = Path(path)
    if p.is_dir():
        parts = []
        for f in sorted(p.glob("*.py")):
            if f.name in ("__init__.py", "conftest.py"):
                continue
            if filter_files and f.name not in filter_files:
                continue
            parts.append(f"# === {f.name} ===\n{f.read_text(encoding='utf-8')}")
        return "\n\n".join(parts)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main():
    state_path = PIPELINE_STATE

    if not state_path.exists():
        print("[오류] state/pipeline.json 없음.")
        sys.exit(1)

    state = read_state(state_path)
    heal_context = state.get("heal_context")

    if not heal_context:
        print("[오류] heal_context 없음. 06_heal.py를 먼저 실행하세요.")
        sys.exit(1)

    if state.get("step") != "heal_needed":
        print("[스킵] heal_needed 상태가 아님.")
        sys.exit(0)

    generated_path = state.get("generated_file_path", DEFAULT_GENERATED_FILE)

    # 실패 파일만 필터링 (힐링 시 전체 120개 대신 실패 3-5개만 Agent에 전달)
    failures = heal_context.get("failures", [])
    failed_filenames = set()
    for f in failures:
        test_id = f.get("test_id", "")
        if "::" in test_id:
            fname = Path(test_id.split("::")[0]).name
            failed_filenames.add(fname)

    # 모든 컨텍스트 파일 병렬 읽기 (프로젝트 루트 기준 절대 경로)
    project_root = Path(__file__).parent.parent
    paths = {
        "team_charter":    project_root / "agents/team_charter.md",
        "senior_role":     project_root / "agents/roles/senior.md",
        "junior_role":     project_root / "agents/roles/junior.md",
        "lessons_learned": project_root / "agents/lessons_learned.md",
    }
    with ThreadPoolExecutor() as ex:
        futures = {k: ex.submit(read_file, v) for k, v in paths.items()}
        # generated_code는 실패 파일만 포함
        futures["generated_code"] = ex.submit(
            read_file, generated_path,
            failed_filenames if failed_filenames else None,
        )
        ctx = {k: f.result() for k, f in futures.items()}

    heal_count = heal_context.get("heal_count", 1)

    # 실패 스크린샷 경로 수집 (힐링 시 시각 검증용)
    failures = heal_context.get("failures", [])
    screenshots = {}
    for f in failures:
        shot = f.get("screenshot")
        if shot and shot.get("path"):
            screenshots[f["test_name"]] = shot

    # heal_stats.json에서 Top 5 빈출 패턴 로드
    top_heal_patterns = []
    try:
        if HEAL_STATS_PATH.exists():
            stats = read_state(HEAL_STATS_PATH)
            patterns = stats.get("patterns", {})
            sorted_patterns = sorted(
                patterns.values(), key=lambda p: p["count"], reverse=True
            )
            top_heal_patterns = sorted_patterns[:5]
    except Exception:
        pass

    assertion_integrity = state.get("assertion_integrity")

    context_payload = {
        "stage": "healing",
        "url": state["url"],
        "generated_file_path": generated_path,
        "generated_code": ctx["generated_code"],
        "heal_context": heal_context,
        "dom_info": state.get("dom_info", {}),
        "team_charter": ctx["team_charter"],
        "senior_role": ctx["senior_role"],
        "junior_role": ctx["junior_role"],
        "lessons_learned": ctx["lessons_learned"],
        "screenshots": screenshots,
        "top_heal_patterns": top_heal_patterns,
        "assertion_integrity": assertion_integrity,
        "mcp_instructions": {
            "when": "traceback만으로 원인 불명확한 Locator/Assertion/Timeout 오류 시",
            "steps": [
                "1. Read tool로 screenshot.path 파일 열기 → 실패 시점 화면 확인",
                "2. Playwright_navigate → URL 접속 (필요 시)",
                "3. playwright_get_visible_html → 현재 DOM 구조 확인",
                "4. playwright_get_visible_text → 현재 페이지 텍스트 확인",
                "5. Playwright_evaluate → document.querySelector() 로 셀렉터 검증",
            ],
            "url": state.get("url", ""),
            "note": "MCP 브라우저와 pytest 브라우저는 별개 세션 (쿠키 비공유)",
        },
    }

    print(f"[06a] 힐링 심의 컨텍스트 준비 완료 ({heal_count}회차)")
    print(f"  실패 케이스: {len(failures)}건")
    if screenshots:
        print(f"  스크린샷: {len(screenshots)}개 (시각 검증 가능)")
    if top_heal_patterns:
        print(f"  빈출 패턴: {len(top_heal_patterns)}개 (Top 5 주입)")
    if assertion_integrity and assertion_integrity.get("has_warnings"):
        print(f"  ⚠️  assertion 약화 경고: {len(assertion_integrity['warnings'])}건 (심의 Agent에 전달됨)")
    for i, f in enumerate(failures[:3], 1):
        print(f"    [{i}] {f.get('test_name', 'unknown')}")
    print()
    print("=== DELIBERATION_CONTEXT_START ===")
    print(json.dumps(context_payload, ensure_ascii=False))
    print("=== DELIBERATION_CONTEXT_END ===")


if __name__ == "__main__":
    main()
