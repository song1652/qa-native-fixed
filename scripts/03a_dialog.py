"""
Step 3a -- 코드 리뷰 컨텍스트 준비 (P64: 페르소나 제거)
LLM 없음. Claude Code가 코드 리뷰를 직접 수행하기 위한 컨텍스트를 수집·출력한다.
team_charter/senior/junior 페르소나 텍스트 제거 → generated_code + lint + plan + lessons_learned 만 포함.
결과는 state.json에만 저장 (dialog.json은 팀 토론 전용).
"""
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from _paths import PIPELINE_STATE, read_state
from _constants import DEFAULT_GENERATED_FILE
from _pipeline_registry import Step  # P80: step 검증용


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

    # P80: 단계 검증 — REVIEWED(린트 완료) 이후에만 실행이 의미 있다.
    current_step = state.get("step", "")
    if current_step and current_step not in {Step.REVIEWED, Step.GENERATED}:
        print(f"[03a] [경고] 현재 step={current_step!r} — 03a_dialog는 reviewed 직후에 실행하세요.")

    if not state.get("lint_result"):
        print("[오류] lint_result 없음. 03_lint.py를 먼저 실행하세요.")
        sys.exit(1)

    # 리뷰에 필요한 파일만 병렬 읽기 — 페르소나 파일(team_charter/senior/junior) 제거 (P64)
    project_root = Path(__file__).parent.parent
    paths = {
        "lessons_learned": project_root / "agents/lessons_learned.md",
        "generated_code":  generated_path,
    }
    with ThreadPoolExecutor() as ex:
        futures = {k: ex.submit(read_file, v) for k, v in paths.items()}
        ctx = {k: f.result() for k, f in futures.items()}

    lint = state["lint_result"]
    # 코드 리뷰 체크리스트 기반 컨텍스트 (페르소나 텍스트 없음)
    context_payload = {
        "stage": "review",
        "url": state["url"],
        "generated_file_path": generated_path,
        "generated_code": ctx["generated_code"],
        "lint_result": lint,
        "plan": state.get("plan", []),
        "lessons_learned": ctx["lessons_learned"],
    }

    lint_status = "통과" if lint.get("passed") else f"이슈 {lint.get('issue_count', 0)}건"
    print("[03a] 코드 리뷰 컨텍스트 준비 완료")
    print(f"  생성 파일: {generated_path}")
    print(f"  Lint 결과: {lint_status}")
    print()
    print("=== DELIBERATION_CONTEXT_START ===")
    print(json.dumps(context_payload, ensure_ascii=False))
    print("=== DELIBERATION_CONTEXT_END ===")


if __name__ == "__main__":
    main()
