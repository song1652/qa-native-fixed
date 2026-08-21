"""파이프라인 종료 코드 상수 및 step 전이 규칙."""

# 공통
EXIT_SUCCESS = 0          # 정상 완료
EXIT_ERROR = 1            # 일반 오류

# 힐링 (06_heal.py, 99_merge.py)
EXIT_HEAL_NEEDED = 10     # 실패 정보 저장 → Claude Code 패치 필요
EXIT_HEAL_EXCEEDED = 2    # 최대 힐링 횟수 초과
MAX_HEAL = 3              # 최대 힐링 횟수 (단일/병렬 파이프라인 공통)

# 승인 (04_approve.py)
EXIT_REJECTED = 2         # 반려 → 코드 재작성
EXIT_AWAITING_APPROVAL = 3  # 대시보드 승인 대기

# ── Step 전이 규칙 ──────────────────────────────────────────────
# {current_step: [allowed_next_steps]}
VALID_TRANSITIONS = {
    "init":         ["analyzed"],
    "analyzed":     ["planned", "generated"],  # planned: 심의 Agent가 plan 저장 시 경유하는 선택적 중간 단계
    "planned":      ["generated"],
    "generated":    ["reviewed"],
    "reviewed":     ["done", "heal_needed", "timeout"],
    "done":         ["heal_needed"],
    "heal_needed":  ["done", "heal_failed", "timeout"],
    "heal_failed":  [],           # 종료 상태
    "timeout":      ["done", "heal_needed"],  # 재실행 가능
}


def assert_valid_transition(current: str, next_step: str) -> None:
    """step 전이가 허용되는지 검증. 잘못된 전이 시 ValueError."""
    allowed = VALID_TRANSITIONS.get(current)
    if allowed is None:
        return  # 알 수 없는 step이면 검증 건너뜀 (하위 호환)
    if next_step not in allowed:
        raise ValueError(
            f"잘못된 step 전이: '{current}' → '{next_step}'. "
            f"허용: {allowed}. "
            f"파이프라인 단계가 건너뛰어졌을 수 있습니다. "
            f"state/pipeline.json을 확인하세요."
        )
