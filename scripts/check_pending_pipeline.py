"""
UserPromptSubmit 훅에서 실행됨.
state/pipeline.json의 step=init이고 url이 있으면
대시보드에서 run_qa.py가 실행된 것이므로 파이프라인 시작을 Claude에 요청한다.

트리거 조건: Step.INIT (레지스트리 상수) — P44
실행 지시문: remaining_steps_hint()가 PIPELINE_STEP_DEFS 기반으로 자동 생성.
"""
import sys
from _paths import PIPELINE_STATE
from _pipeline_registry import Step
from hook_utils import check_state, remaining_steps_hint


def _pipeline_ready(s: dict) -> bool:
    # url이 있어야 대시보드에서 실행한 것 (초기화 상태와 구분)
    if not s.get("url", ""):
        return False
    # dom_info가 이미 있으면 01_analyze 완료된 것 → 중복 방지
    if s.get("dom_info"):
        return False
    return True


state = check_state(PIPELINE_STATE, key="step", value=Step.INIT, extra_check=_pipeline_ready)
if state is None:
    sys.exit(0)

url = state.get("url", "")
case_count = len(state.get("test_cases", []))

lines = [
    "[파이프라인 자동 실행] 대시보드에서 run_qa.py가 실행되었습니다.",
    f"URL: {url}",
    f"케이스: {case_count}개",
    "",
    "CLAUDE.md 파이프라인의 1번 단계부터 실행해주세요:",
] + remaining_steps_hint(Step.INIT)

print("\n".join(lines))
