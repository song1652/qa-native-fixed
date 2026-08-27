"""
UserPromptSubmit 훅에서 실행됨.
state/parallel.json의 status=ready이면 subagent 실행 요청을
stdout으로 출력해 Claude 컨텍스트에 주입한다.

트리거 조건: ParallelStatus.READY (레지스트리 상수) — P44
P89: 로그 파일 스크레이핑 대신 state/parallel.json의 subagent_contexts 키를 읽음
"""
import json
import sys
from _paths import PARALLEL_STATE
from _pipeline_registry import ParallelStatus
from hook_utils import check_state

state = check_state(PARALLEL_STATE, key="status", value=ParallelStatus.READY)
if state is None:
    sys.exit(0)

total = state.get("total_count", 0)
targets = state.get("targets", [])

# state/parallel.json의 subagent_contexts에서 PARALLEL_SUBAGENT_CONTEXTS 읽기 (P89)
contexts_json = ""
subagent_contexts = state.get("subagent_contexts")
if subagent_contexts:
    contexts_json = json.dumps(subagent_contexts, ensure_ascii=False, indent=2)

lines = [
    f"[병렬 파이프라인 자동 실행] state/parallel.json에 ready 상태가 감지되었습니다. 즉시 subagent를 실행해주세요.",
    f"대상: {total}개 테스트 파일",
    "",
    "대상 목록:",
]
for t in targets:
    lines.append(f"  - [{t.get('group_label', '')}] {t.get('url', '')} → {t.get('output_path', '')}")

if contexts_json:
    lines += [
        "",
        "=== PARALLEL_SUBAGENT_CONTEXTS_START ===",
        contexts_json,
        "=== PARALLEL_SUBAGENT_CONTEXTS_END ===",
    ]

lines += [
    "",
    "진행 방법: CLAUDE.md의 '병렬 파이프라인' 지침을 따라 실행하세요.",
    "1. 위 PARALLEL_SUBAGENT_CONTEXTS에서 shared_context_paths의 파일들은 각 subagent가 직접 읽어 참조",
    "2. subagents 배열의 각 항목을 Agent tool로 동시에 실행",
    "3. 각 subagent는 dom_info와 test_cases를 바탕으로 Playwright 테스트 코드 작성 → output_path에 저장",
    "4. 모든 subagent 완료 후 python parallel/99_merge.py 실행",
    "5. 완료 후 state/parallel.json의 status를 'done'으로 변경",
]

print("\n".join(lines))
