"""
UserPromptSubmit 훅에서 실행됨.
state/quick.json 또는 state/parallel.json의 status=heal_needed이면
HEAL_SUBAGENT_CONTEXTS를 stdout으로 출력해 Claude 컨텍스트에 주입한다.

트리거 조건: ParallelStatus.HEAL_NEEDED (레지스트리 상수) — P44
P76: state/parallel.json도 감지 대상에 추가 (99_merge.py 실행 후 heal_needed 자동 감지)
"""
import sys
from _paths import QUICK_STATE, QUICK_RUN_LOG, PARALLEL_STATE, RUN_PARALLEL_LOG
from _pipeline_registry import ParallelStatus
from hook_utils import check_state

# 1. quick.json 우선 확인
state = check_state(QUICK_STATE, key="status", value=ParallelStatus.HEAL_NEEDED)
log_path = QUICK_RUN_LOG
pipeline_label = "빠른 실행"
restart_cmd = ""  # 아래에서 설정

# 2. quick.json이 해당 없으면 parallel.json 확인 (P76)
if state is None:
    state = check_state(PARALLEL_STATE, key="status", value=ParallelStatus.HEAL_NEEDED)
    if state is not None:
        log_path = RUN_PARALLEL_LOG
        pipeline_label = "병렬"

if state is None:
    sys.exit(0)

failed = state.get("execution_result", {}).get("failed", 0)
groups = state.get("groups", []) or list(state.get("execution_result", {}).get("group_results", {}).keys())

# 로그 파일에서 HEAL_SUBAGENT_CONTEXTS 추출
contexts_json = ""
if log_path.exists():
    log_text = log_path.read_text(encoding="utf-8")
    start_marker = "=== HEAL_SUBAGENT_CONTEXTS_START ==="
    end_marker = "=== HEAL_SUBAGENT_CONTEXTS_END ==="
    start_idx = log_text.rfind(start_marker)  # 가장 최근 힐링 컨텍스트
    end_idx = log_text.rfind(end_marker)
    if start_idx != -1 and end_idx != -1:
        contexts_json = log_text[start_idx + len(start_marker):end_idx].strip()

if not contexts_json:
    sys.exit(0)

# 재실행 명령 결정
if log_path == RUN_PARALLEL_LOG:
    group_args = " --group " + " ".join(groups) if groups else ""
    restart_cmd = f"python parallel/99_merge.py{group_args}"
else:
    group_args = " --group " + " ".join(groups) if groups else ""
    restart_cmd = f"python parallel/99_merge.py --quick{group_args}"

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
