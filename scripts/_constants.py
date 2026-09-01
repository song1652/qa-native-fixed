"""파이프라인 종료 코드 상수 및 step 전이 규칙.

VALID_TRANSITIONS / VALID_PARALLEL_TRANSITIONS / assert_valid_transition /
assert_valid_parallel_transition 은 _pipeline_registry.py가 단일 소스다 (P35).
이 모듈은 하위 호환을 위해 re-export만 한다 — 직접 수정하지 말 것.
"""

# 공통
EXIT_SUCCESS = 0          # 정상 완료
EXIT_ERROR = 1            # 일반 오류

# 힐링 (06_heal.py, 99_merge.py)
EXIT_HEAL_NEEDED = 10     # 실패 정보 저장 → Claude Code 패치 필요
EXIT_HEAL_EXCEEDED = 2    # 최대 힐링 횟수 초과
MAX_HEAL = 3              # 최대 힐링 횟수 (단일/병렬 파이프라인 공통)

# 승인 (04_approve.py)
EXIT_REJECTED = 4         # 반려 → 코드 재작성 (P59: EXIT_HEAL_EXCEEDED=2와 충돌 해소)
EXIT_HEAL_SKIPPED = 3  # 06_auto_heal: 실행 조건 불충족 (heal_needed 아님) — no-op

# ── 생성 테스트 경로 기본값 ──────────────────────────────────────
# state의 generated_file_path가 비었을 때 쓰는 fallback.
DEFAULT_GENERATED_DIR = "tests/generated/"
DEFAULT_GENERATED_FILE = "tests/generated/test_generated.py"

# ── pytest 실행 파라미터 ────────────────────────────────────────
# 두 값은 의도적으로 다르다:
#   05_execute.py — 실제 테스트 실행. 브라우저 세션 수를 감안해 보수적으로 4.
#   06_heal.py    — 실패 정보 수집용 재실행. 수집만 하므로 더 공격적으로 8.
MAX_PYTEST_WORKERS = 4
HEAL_PYTEST_WORKERS = 8

# 06_heal.py fallback 재실행 타임아웃(초)
PYTEST_HEAL_TIMEOUT_SEC = 600

# ── Step 전이 규칙 + 검증 함수 (단일/병렬) ────────────────────────
# 단일 소스는 _pipeline_registry.py. 이 모듈은 하위 호환 re-export만 제공.
# ── pytest 종료 코드 정책 (M-2/P119) ──────────────────────────────────────
# 0=전체 통과, 1=실패 있음 — 둘 다 정상 pytest 종료. 이외(2=내부오류, 3=중단, 4=사용오류)는 비정상.
# 단일(05_execute.py)과 병렬(99_merge.py) 파이프라인이 공통으로 사용.
PYTEST_NORMAL_EXIT_CODES: frozenset = frozenset({0, 1})

from _pipeline_registry import (       # noqa: E402
    VALID_TRANSITIONS,
    VALID_PARALLEL_TRANSITIONS,
    assert_valid_transition,
    assert_valid_parallel_transition,
    RESETTABLE_STEPS,
    RESETTABLE_PARALLEL_STATUSES,
)
