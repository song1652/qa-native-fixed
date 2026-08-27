"""
Step 2a -- Plan 컨텍스트 준비 (P64: 페르소나 제거)
LLM 없음. Claude Code가 plan을 직접 생성하기 위한 컨텍스트를 수집·출력한다.
team_charter/senior/junior 페르소나 텍스트 제거 → dom_info + test_cases + lessons_learned 만 포함.
결과는 state.json에만 저장 (dialog.json은 팀 토론 전용).
"""
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from _paths import PIPELINE_STATE, read_state, resolve_sub_doms
from _pipeline_registry import Step  # P80: step 검증용


def read_file(path):
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def main():
    state_path = PIPELINE_STATE

    if not state_path.exists():
        print("[오류] state/pipeline.json 없음.")
        sys.exit(1)

    state = read_state(state_path)

    # P80: 단계 검증 — 이미 plan이 완성된 상태에서 재실행되면 plan을 덮어쓸 위험.
    # analyzed/init 이후에만 실행이 의미 있다.
    current_step = state.get("step", "")
    _allowed = {Step.INIT, Step.ANALYZED}
    if current_step and current_step not in _allowed:
        print(f"[02a] [경고] 현재 step={current_step!r} — 02a_dialog는 analyzed 직후에 실행하세요.")
        print(f"     (이미 plan이 있으면 덮어쓰일 수 있습니다. 강제 진행하려면 이 경고를 무시하세요.)")

    if not state.get("dom_info"):
        print("[오류] dom_info 없음. 01_analyze.py를 먼저 실행하세요.")
        sys.exit(1)

    # lessons_learned만 읽음 — 페르소나 파일(team_charter/senior/junior) 제거 (P64)
    project_root = Path(__file__).parent.parent
    lessons_path = project_root / "agents/lessons_learned.md"
    lessons_learned = read_file(lessons_path)

    # 서브페이지 DOM 캐시 일괄 로드 (agent가 개별 파일 읽기 불필요)
    sub_doms_raw = resolve_sub_doms(state)
    # 경량화: 셀렉터 관련 필드만 추출
    sub_doms = {}
    for url, dom in sub_doms_raw.items():
        sub_doms[url] = {
            k: dom.get(k)
            for k in ("title", "url", "inputs", "buttons", "components",
                       "idElements", "forms_count")
            if dom.get(k) is not None
        }

    # plan 생성에 필요한 핵심 컨텍스트만 포함 (페르소나 텍스트 없음)
    context_payload = {
        "stage": "planning",
        "url": state["url"],
        "dom_info": state["dom_info"],
        "sub_doms": sub_doms,
        "test_cases": state["test_cases"],
        "lessons_learned": lessons_learned,
    }

    print("[02a] Plan 컨텍스트 준비 완료")
    print(f"  URL: {state['url']}")
    print(f"  DOM 입력필드: {len(state['dom_info'].get('inputs', []))}개  "
          f"버튼: {len(state['dom_info'].get('buttons', []))}개")
    if sub_doms:
        print(f"  서브페이지 DOM: {len(sub_doms)}개 (컨텍스트에 포함)")
    print(f"  테스트 케이스: {len(state['test_cases'])}개")
    print()
    print("=== DELIBERATION_CONTEXT_START ===")
    print(json.dumps(context_payload, ensure_ascii=False))
    print("=== DELIBERATION_CONTEXT_END ===")


if __name__ == "__main__":
    main()
