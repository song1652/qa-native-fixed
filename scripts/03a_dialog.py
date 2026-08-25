"""
Step 3a -- 코드 리뷰 심의 컨텍스트 준비
LLM 없음. 심의 agent에 전달할 컨텍스트를 수집·출력한다.
결과는 state.json에만 저장 (dialog.json은 팀 토론 전용).
모든 파일 읽기를 이 스크립트에서 처리 → agent는 파일 읽기 없이 바로 심의 시작.
"""
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from _paths import PIPELINE_STATE, read_state
from _constants import DEFAULT_GENERATED_FILE


def read_file(path):
    p = Path(path)
    if p.is_dir():
        parts = []
        for f in sorted(p.glob("*.py")):
            if f.name not in ("__init__.py", "conftest.py"):
                parts.append(f"# === {f.name} ===\n{f.read_text(encoding='utf-8')}")
        return "\n\n".join(parts)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main():
    state_path = PIPELINE_STATE

    if not state_path.exists():
        print("[오류] state/pipeline.json 없음.")
        sys.exit(1)

    state = read_state(state_path)
    generated_path = state.get("generated_file_path", DEFAULT_GENERATED_FILE)

    if not state.get("lint_result"):
        print("[오류] lint_result 없음. 03_lint.py를 먼저 실행하세요.")
        sys.exit(1)

    # 모든 컨텍스트 파일 병렬 읽기 (프로젝트 루트 기준 절대 경로)
    project_root = Path(__file__).parent.parent
    paths = {
        "team_charter":    project_root / "agents/team_charter.md",
        "senior_role":     project_root / "agents/roles/senior.md",
        "junior_role":     project_root / "agents/roles/junior.md",
        "lessons_learned": project_root / "agents/lessons_learned.md",
        "generated_code":  generated_path,
    }
    with ThreadPoolExecutor() as ex:
        futures = {k: ex.submit(read_file, v) for k, v in paths.items()}
        ctx = {k: f.result() for k, f in futures.items()}

    lint = state["lint_result"]
    context_payload = {
        "stage": "review",
        "url": state["url"],
        "generated_file_path": generated_path,
        "generated_code": ctx["generated_code"],
        "lint_result": lint,
        "plan": state.get("plan", []),
        "team_charter": ctx["team_charter"],
        "senior_role": ctx["senior_role"],
        "junior_role": ctx["junior_role"],
        "lessons_learned": ctx["lessons_learned"],
    }

    lint_status = "통과" if lint.get("passed") else f"이슈 {lint.get('issue_count', 0)}건"
    print("[03a] 코드 리뷰 심의 컨텍스트 준비 완료")
    print(f"  생성 파일: {generated_path}")
    print(f"  Lint 결과: {lint_status}")
    print()
    print("=== DELIBERATION_CONTEXT_START ===")
    print(json.dumps(context_payload, ensure_ascii=False))
    print("=== DELIBERATION_CONTEXT_END ===")


if __name__ == "__main__":
    main()
