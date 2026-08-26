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
    extra_check=lambda s: not s.get("execution_result"),
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
] + remaining_steps_hint(Step.REVIEWED)

print("\n".join(lines))
