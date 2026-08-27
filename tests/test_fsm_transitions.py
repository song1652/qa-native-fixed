"""FSM 전이 안전장치 단위 테스트.

테스트 대상 (_constants.py):
- assert_valid_transition          — pipeline.json의 step 전이
- assert_valid_parallel_transition — parallel.json / quick.json의 status 전이

두 함수는 파이프라인 단계 건너뛰기를 막는 마지막 방어선이라,
"허용 전이는 통과 / 미허용 전이는 ValueError / 모르는 상태는 건너뜀"
세 가지 계약을 모두 고정한다.
"""
import sys
from pathlib import Path

import pytest

# scripts/ 모듈 import 준비
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from _constants import (  # noqa: E402
    VALID_TRANSITIONS,
    VALID_PARALLEL_TRANSITIONS,
    assert_valid_transition,
    assert_valid_parallel_transition,
)


def _declared_pairs(table: dict) -> list:
    """{현재: [허용된 다음]} → [(현재, 다음), ...] 평탄화."""
    return [(cur, nxt) for cur, allowed in table.items() for nxt in allowed]


def _undeclared_pairs(table: dict) -> list:
    """선언되지 않은 (현재, 다음) 조합. 단, 현재는 표에 존재하는 상태여야 한다."""
    states = set(table) | {n for a in table.values() for n in a}
    return [
        (cur, nxt)
        for cur, allowed in table.items()
        for nxt in sorted(states)
        if nxt not in allowed and nxt != ""
    ]


# ── step 전이 (pipeline.json) ────────────────────────────────────


class TestAssertValidTransition:
    """assert_valid_transition: step 전이 검증."""

    @pytest.mark.parametrize(
        "current,next_step",
        _declared_pairs(VALID_TRANSITIONS),
        ids=lambda v: str(v),
    )
    def test_declared_transition_passes(self, current, next_step):
        """표에 선언된 전이는 예외 없이 통과해야 한다."""
        assert_valid_transition(current, next_step)

    @pytest.mark.parametrize(
        "current,next_step",
        _undeclared_pairs(VALID_TRANSITIONS),
        ids=lambda v: str(v),
    )
    def test_undeclared_transition_raises(self, current, next_step):
        """표에 없는 전이는 전부 ValueError."""
        with pytest.raises(ValueError):
            assert_valid_transition(current, next_step)

    def test_stage_skip_is_rejected(self):
        """이 안전장치의 존재 이유: 단계 건너뛰기 차단 (init → generated)."""
        with pytest.raises(ValueError):
            assert_valid_transition("init", "generated")

    def test_self_transition_rejected(self):
        """같은 step으로의 자기 전이는 선언돼 있지 않으므로 거부."""
        with pytest.raises(ValueError):
            assert_valid_transition("init", "init")

    def test_unknown_current_step_is_skipped(self):
        """알 수 없는 current는 하위 호환을 위해 검증을 건너뛴다 (예외 없음)."""
        assert_valid_transition("존재하지_않는_step", "generated")
        assert_valid_transition("", "generated")

    def test_error_message_has_debugging_context(self):
        """오류 메시지에 현재/다음/허용목록이 모두 담겨야 디버깅이 된다."""
        with pytest.raises(ValueError) as exc:
            assert_valid_transition("init", "done")
        msg = str(exc.value)
        assert "init" in msg
        assert "done" in msg
        assert "analyzed" in msg          # 허용 목록
        assert "pipeline.json" in msg     # 확인할 파일 안내


# ── parallel status 전이 (parallel.json / quick.json) ────────────


class TestAssertValidParallelTransition:
    """assert_valid_parallel_transition: 병렬 파이프라인 status 전이 검증."""

    @pytest.mark.parametrize(
        "current,next_status",
        _declared_pairs(VALID_PARALLEL_TRANSITIONS),
        ids=lambda v: str(v),
    )
    def test_declared_transition_passes(self, current, next_status):
        assert_valid_parallel_transition(current, next_status)

    @pytest.mark.parametrize(
        "current,next_status",
        _undeclared_pairs(VALID_PARALLEL_TRANSITIONS),
        ids=lambda v: str(v),
    )
    def test_undeclared_transition_raises(self, current, next_status):
        with pytest.raises(ValueError):
            assert_valid_parallel_transition(current, next_status)

    def test_empty_initial_status_is_validated(self):
        """빈 status("")는 표에 키로 존재하므로 '모르는 상태'가 아니라 검증 대상이다.

        단, 호출부(_validate_transition_locked / _validate_transition_locked_raw)는
        current_val이 falsy면 의도적으로 조기 return하므로 이 규칙은 실제
        파이프라인에서는 발동하지 않는다("초기 상태에서는 검증 건너뜀" 주석 참조).
        즉 표의 "" 항목은 사실상 죽은 설정이다. 여기서는 함수 자체의 계약만 고정한다.

        그래도 표에서 지우지는 않는다. 지우면 ""가 "알 수 없는 status"가 되어
        아래 test_unknown_current_status_is_skipped처럼 무검증으로 바뀌고,
        이 테스트의 ""→done ValueError 기대가 사라진다(_constants.py 주석 참조).
        """
        assert_valid_parallel_transition("", "init")     # 허용
        assert_valid_parallel_transition("", "testing")  # 허용
        with pytest.raises(ValueError):
            assert_valid_parallel_transition("", "done")

    def test_unknown_current_status_is_skipped(self):
        assert_valid_parallel_transition("존재하지_않는_status", "done")

    def test_error_message_points_at_parallel_state_files(self):
        with pytest.raises(ValueError) as exc:
            assert_valid_parallel_transition("ready", "done")
        msg = str(exc.value)
        assert "ready" in msg
        assert "done" in msg
        assert "parallel.json" in msg or "quick.json" in msg


# ── 전이표 자체의 무결성 ─────────────────────────────────────────


class TestTransitionTableIntegrity:
    """표에 오타가 나면 그 상태로의 전이가 조용히 무검증이 되므로 구조를 고정한다."""

    @pytest.mark.parametrize(
        "table_name,table",
        [
            ("VALID_TRANSITIONS", VALID_TRANSITIONS),
            ("VALID_PARALLEL_TRANSITIONS", VALID_PARALLEL_TRANSITIONS),
        ],
    )
    def test_every_next_state_is_a_known_key(self, table_name, table):
        """다음 상태는 전부 표의 키여야 한다.

        키에 없는 상태로 전이하면 그 다음 전이부터 get()이 None을 반환해
        검증이 통째로 비활성화된다 (오타 → 안전장치 무력화).
        """
        keys = set(table)
        unknown = {
            nxt for allowed in table.values() for nxt in allowed if nxt not in keys
        }
        assert not unknown, f"{table_name}: 키에 없는 다음 상태 {sorted(unknown)}"

    @pytest.mark.parametrize(
        "table_name,table",
        [
            ("VALID_TRANSITIONS", VALID_TRANSITIONS),
            ("VALID_PARALLEL_TRANSITIONS", VALID_PARALLEL_TRANSITIONS),
        ],
    )
    def test_no_duplicate_or_self_referential_entries(self, table_name, table):
        """허용 목록에 중복이 없어야 한다 (자기 자신 포함 여부는 표의 의도대로 유지)."""
        for cur, allowed in table.items():
            assert len(allowed) == len(set(allowed)), (
                f"{table_name}['{cur}']에 중복 항목: {allowed}"
            )


# ── 핵심 경로 고정 ───────────────────────────────────────────────


def _walk(checker, chain: list) -> None:
    """상태 체인을 순서대로 전이시키며 전부 허용되는지 확인."""
    for cur, nxt in zip(chain, chain[1:]):
        checker(cur, nxt)


class TestCriticalPathsArePreserved:
    """실제 파이프라인이 밟는 경로를 표와 독립적으로 고정한다.

    위쪽 parametrize 테스트는 전이표에서 파생되므로, 표가 잘못 수정되면
    기대값도 함께 바뀌어 회귀를 놓친다. 여기서는 경로를 하드코딩해
    표에서 핵심 전이가 사라지면 실패하게 만든다.
    """

    def test_happy_path(self):
        _walk(assert_valid_transition,
              ["init", "analyzed", "generated", "reviewed", "done"])

    def test_happy_path_via_planned(self):
        """planned는 02a_dialog 심의 Agent가 plan을 저장할 때 경유하는 선택적 단계.
        C-1(P97): prompts/plan_deliberation.md가 step=planned를 지시하므로 FSM 복원.
        """
        _walk(assert_valid_transition,
              ["init", "analyzed", "planned", "generated", "reviewed"])

    def test_heal_path(self):
        _walk(assert_valid_transition, ["reviewed", "heal_needed", "done"])

    def test_heal_failure_then_rerun(self):
        _walk(assert_valid_transition,
              ["heal_needed", "heal_failed", "analyzed"])

    def test_timeout_path(self):
        _walk(assert_valid_transition, ["reviewed", "timeout", "heal_needed"])

    def test_rerun_reset_paths(self):
        """재실행 전체 리셋: done/heal_failed/timeout에서 init으로 돌아갈 수 있어야 한다."""
        for src in ("done", "heal_failed", "timeout"):
            assert_valid_transition(src, "init")

    def test_parallel_happy_path(self):
        _walk(assert_valid_parallel_transition,
              ["", "init", "analyzing", "ready", "testing", "done"])

    def test_parallel_heal_path(self):
        _walk(assert_valid_parallel_transition,
              ["testing", "heal_needed", "done"])

    def test_parallel_error_recovery(self):
        _walk(assert_valid_parallel_transition, ["init", "analyzing", "error", "init"])

    # ── C-1/C-2/C-3 경로 (HEAL_FAILED/TIMEOUT/ERROR 커버) ─────────

    def test_timeout_to_heal_failed(self):
        """C-2: timeout 후 heal_failed로 직행할 수 있어야 한다."""
        assert_valid_transition("timeout", "heal_failed")

    def test_heal_failed_to_done(self):
        """C-2: heal_failed 상태에서 done으로 전이 (부분 통과 처리)."""
        assert_valid_transition("heal_failed", "done")

    def test_heal_failed_to_heal_needed(self):
        """C-2: heal_failed 후 heal_needed로 재시도 경로."""
        assert_valid_transition("heal_failed", "heal_needed")

    def test_reviewed_to_heal_failed(self):
        """C-2: reviewed에서 사이트 불가 시 즉시 heal_failed."""
        assert_valid_transition("reviewed", "heal_failed")

    def test_parallel_testing_to_error(self):
        """C-1: pytest exit 5(수집 0건) → testing→error 전이."""
        assert_valid_parallel_transition("testing", "error")

    def test_parallel_testing_to_heal_failed(self):
        """C-3: 힐링 불가(사이트 접근 불가/전체 반복) → testing→heal_failed 전이."""
        assert_valid_parallel_transition("testing", "heal_failed")
