"""
UserPromptSubmit 훅에서 실행됨.
state/pipeline.json의 step=reviewed이고 execution_result가 없으면
코드 리뷰가 완료된 것이므로 테스트 실행을 Claude에 요청한다.
(승인 단계 제거 -- 심의 완료 후 바로 실행)

트리거 조건: Step.REVIEWED (레지스트리 상수) — P44
실행 지시문: remaining_steps_hint()가 PIPELINE_STEP_DEFS 기반으로 자동 생성.
"""
import sys
from _paths import PIPELINE_STATE
from _pipeline_registry import Step
from hook_utils import check_state, remaining_steps_hint

state = check_state(
    PIPELINE_STATE,
    key="step",
    value=Step.REVIEWED,
    # L-7(P129): execution_result 조건 제거 — 반려→재생성 후 step=reviewed로 돌아왔을 때
    # 이전 실행 결과가 남아 있어도 훅이 재발동해야 한다.
    # 05_execute가 실행되면 step이 DONE/HEAL_NEEDED로 전이되므로 중복 발동 없음.
)
if state is None:
    sys.exit(0)

url = state.get("url", "")
case_count = len(state.get("test_cases", []))

lines = [
    "[파이프라인 자동 실행] 코드 리뷰가 완료되었습니다.",
    f"URL: {url}",
    f"케이스: {case_count}개",
    "",
    "CLAUDE.md 파이프라인의 실행 단계부터 시작해주세요:",
] + remaining_steps_hint(Step.REVIEWED, start_after_last=True)  # P78: 03a/04 서브 단계 생략

print("\n".join(lines))
