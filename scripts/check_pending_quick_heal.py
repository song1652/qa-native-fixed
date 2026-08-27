"""
UserPromptSubmit 훅에서 실행됨.
state/quick.json 또는 state/parallel.json의 status=heal_needed이면
HEAL_SUBAGENT_CONTEXTS를 stdout으로 출력해 Claude 컨텍스트에 주입한다.

트리거 조건: ParallelStatus.HEAL_NEEDED (레지스트리 상수) — P44
P76: state/parallel.json도 감지 대상에 추가 (99_merge.py 실행 후 heal_needed 자동 감지)
P89: 로그 파일 스크레이핑 대신 상태 파일의 heal_subagent_contexts 키를 읽음
"""
import json
import sys
from _paths import QUICK_STATE, PARALLEL_STATE
from _pipeline_registry import ParallelStatus
from hook_utils import check_state

# 1. quick.json 우선 확인
state = check_state(QUICK_STATE, key="status", value=ParallelStatus.HEAL_NEEDED)
is_quick = state is not None
pipeline_label = "빠른 실행"
restart_cmd = ""  # 아래에서 설정

# 2. quick.json이 해당 없으면 parallel.json 확인 (P76)
if state is None:
    state = check_state(PARALLEL_STATE, key="status", value=ParallelStatus.HEAL_NEEDED)
    if state is not None:
        pipeline_label = "병렬"

if state is None:
    sys.exit(0)

failed = state.get("execution_result", {}).get("failed", 0)
groups = state.get("groups", []) or list(state.get("execution_result", {}).get("group_results", {}).keys())

# 상태 파일의 heal_subagent_contexts에서 HEAL_SUBAGENT_CONTEXTS 읽기 (P89)
contexts_json = ""
heal_contexts = state.get("heal_subagent_contexts")
if heal_contexts:
    contexts_json = json.dumps(heal_contexts, ensure_ascii=False, indent=2)

if not contexts_json:
    sys.exit(0)

# 재실행 명령 결정
group_args = " --group " + " ".join(groups) if groups else ""
if is_quick:
    restart_cmd = f"python parallel/99_merge.py --quick{group_args}"
else:
    restart_cmd = f"python parallel/99_merge.py{group_args}"

lines = [
    f"[{pipeline_label} 힐링 자동 시작] status=heal_needed 상태가 감지되었습니다.",
    f"실패: {failed}건  |  그룹: {', '.join(groups)}",
    "",
    "=== HEAL_SUBAGENT_CONTEXTS_START ===",
    contexts_json,
    "=== HEAL_SUBAGENT_CONTEXTS_END ===",
    "",
    "진행 방법: CLAUDE.md의 '힐링 배치 병렬화' 지침을 따라 실행하세요.",
    "1. 위 HEAL_SUBAGENT_CONTEXTS의 각 배치를 Agent tool로 동시에 실행",
    "2. 각 subagent: 실패 파일 읽기 → traceback 분석 → 패치 → lessons_learned 기록",
    f"3. 모든 배치 완료 후 {restart_cmd} 재실행",
]

print("\n".join(lines))
