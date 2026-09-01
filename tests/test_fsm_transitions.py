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

    def test_done_to_timeout(self):
        """H-1(P104): step=done 후 재실행이 타임아웃되면 done→timeout 전이 필요."""
        assert_valid_transition("done", "timeout")

    def test_heal_failed_to_timeout(self):
        """H-1(P104): step=heal_failed 상태 재실행이 타임아웃 → heal_failed→timeout."""
        assert_valid_transition("heal_failed", "timeout")

    # ── L-4(P114): 누락 경로 5건 ──────────────────────────────────

    def test_reviewed_to_generated(self):
        """P60/P87 반려 후 재작성 경로: reviewed→generated 허용 필요."""
        assert_valid_transition("reviewed", "generated")

    def test_done_to_heal_needed(self):
        """전체 통과 후 일부 TC 추가 힐링 요청 경로: done→heal_needed."""
        assert_valid_transition("done", "heal_needed")

    def test_timeout_to_done(self):
        """타임아웃 후 재실행 성공 경로: timeout→done."""
        assert_valid_transition("timeout", "done")

    def test_parallel_heal_needed_to_testing(self):
        """병렬 힐링 재실행 주경로: heal_needed→testing."""
        assert_valid_parallel_transition("heal_needed", "testing")

    def test_parallel_done_to_testing(self):
        """병렬 전체 통과 후 재실행 경로: done→testing."""
        assert_valid_parallel_transition("done", "testing")


# ── L-4(P114): FSM ↔ 코드 양방향 계약 ──────────────────────────────────────


class TestFsmBidirectionalContract:
    """FSM 전이표와 실제 코드 writer 간 양방향 계약 검증.

    근본 원인 1 차단: "표에만 있고 writer 없는 전이" / "코드가 쓰는데 표에 없는 전이"를
    모두 잡는다. writer 목록은 각 스크립트를 분석해 수동으로 관리한다.

    유지보수 규칙:
        - 새 Step 전이를 쓰는 코드를 추가하면 KNOWN_STEP_WRITERS에도 추가.
        - 새 ParallelStatus 전이를 쓰는 코드를 추가하면 KNOWN_PARALLEL_WRITERS에도 추가.
        - 표에서 전이를 제거하면 여기서도 제거.
    """

    # 자동화된 writer가 없고 대시보드 리셋·사용자 직접 조작으로만 발생하는 전이.
    # FSM에서는 허용하지만 test_all_step_transitions_have_writers 검사에서 면제한다.
    # (M-3/P120: 허위 writer 제거 → 이 집합으로 수동 전이를 명시적으로 선언)
    MANUAL_STEP_TRANSITIONS: frozenset = frozenset({
        ("done",        "analyzed"),    # reset_state() via serve.py 리셋 엔드포인트
        ("done",        "init"),        # 동일
        ("heal_failed", "analyzed"),    # 동일
        ("heal_failed", "init"),        # 동일
        # M-3(P135): heal_failed→done / heal_failed→heal_needed는 05_execute.py가 자동 실행.
        # step=heal_failed ∈ RESETTABLE_STEPS → 05_execute가 heal_count 리셋 후 pytest 실행 →
        # 통과 시 done, 실패 시 heal_needed 로 전이. KNOWN_STEP_WRITERS로 이동.
        ("timeout",     "init"),        # reset_state() via serve.py
    })

    # (from_step, to_step) → writer 스크립트 목록 (자동화된 전이만 등록)
    KNOWN_STEP_WRITERS: dict[tuple[str, str], list[str]] = {
        ("init",        "analyzed"):    ["01_analyze.py"],
        ("analyzed",    "planned"):     ["02a_dialog.py(Agent)"],
        ("analyzed",    "generated"):   ["02_generate.py"],
        ("planned",     "generated"):   ["02_generate.py"],
        ("generated",   "reviewed"):    ["03_lint.py"],
        ("reviewed",    "done"):        ["05_execute.py"],
        ("reviewed",    "heal_needed"): ["05_execute.py"],
        ("reviewed",    "timeout"):     ["05_execute.py"],
        ("reviewed",    "generated"):   ["04_approve.py"],  # P60: 반려→재작성
        ("reviewed",    "heal_failed"): ["06_heal.py"],     # 사이트 불가
        ("done",        "heal_needed"): ["05_execute.py"],
        ("done",        "heal_failed"): ["06_heal.py"],     # over-limit guard
        ("done",        "timeout"):     ["05_execute.py"],  # H-1(P104)
        ("heal_failed", "done"):        ["05_execute.py"],  # M-3(P135): RESETTABLE_STEPS 경로
        ("heal_failed", "heal_needed"): ["05_execute.py"],  # M-3(P135): 동일 — 재실패 시
        ("heal_needed", "done"):        ["05_execute.py"],
        ("heal_needed", "heal_failed"): ["06_heal.py"],
        ("heal_needed", "timeout"):     ["05_execute.py"],
        ("heal_failed", "timeout"):     ["05_execute.py"],  # H-1(P104)
        ("timeout",     "done"):        ["05_execute.py"],
        ("timeout",     "heal_needed"): ["05_execute.py"],
        ("timeout",     "heal_failed"): ["06_heal.py"],     # M-2(P108)
    }

    # (from_status, to_status) → writer 스크립트 목록
    KNOWN_PARALLEL_WRITERS: dict[tuple[str, str], list[str]] = {
        ("",            "init"):        ["run_qa_parallel.py"],
        ("",            "testing"):     ["99_merge.py"],
        ("init",        "analyzing"):   ["run_qa_parallel.py"],
        ("init",        "testing"):     ["99_merge.py"],
        ("analyzing",   "ready"):       ["run_qa_parallel.py"],
        ("analyzing",   "testing"):     ["99_merge.py"],
        ("analyzing",   "error"):       ["run_qa_parallel.py"],
        ("ready",       "testing"):     ["99_merge.py"],
        ("error",       "init"):        ["run_qa_parallel.py(reset)"],
        ("error",       "testing"):     ["99_merge.py"],
        ("testing",     "done"):        ["99_merge.py"],
        ("testing",     "heal_needed"): ["99_merge.py"],
        ("testing",     "heal_failed"): ["99_merge.py"],
        ("testing",     "error"):       ["99_merge.py"],    # C-2(P103)
        ("done",        "testing"):     ["99_merge.py"],
        ("done",        "init"):        ["run_qa_parallel.py(reset)"],
        ("heal_needed", "done"):        ["99_merge.py"],
        ("heal_needed", "heal_failed"): ["99_merge.py"],
        ("heal_needed", "testing"):     ["99_merge.py"],    # L-4(P114)
        ("heal_failed", "testing"):     ["99_merge.py"],
        ("heal_failed", "init"):        ["run_qa_parallel.py(reset)"],
    }

    def test_all_step_transitions_have_writers(self):
        """FSM 전이표의 모든 (from, to) 쌍에 writer가 등록되어 있어야 한다.

        표에만 있고 writer가 없으면 "FSM은 허용하지만 실제로 발생하지 않는 전이"로
        C-1(P102) · H-1(P104) · M-2(P108) 같은 조용한 버그가 숨을 수 있다.

        M-3(P120): MANUAL_STEP_TRANSITIONS에 선언된 수동 전이는 자동화 writer가 없으므로
        이 검사에서 면제한다 (허위 writer 대신 명시적 면제 목록으로 관리).
        """
        missing = []
        for from_step, allowed in VALID_TRANSITIONS.items():
            for to_step in allowed:
                if (from_step, to_step) not in self.KNOWN_STEP_WRITERS:
                    if (from_step, to_step) not in self.MANUAL_STEP_TRANSITIONS:
                        missing.append((from_step, to_step))
        assert not missing, (
            "다음 전이에 writer가 등록되지 않았습니다 — KNOWN_STEP_WRITERS 또는 "
            "MANUAL_STEP_TRANSITIONS에 추가하세요:\n"
            + "\n".join(f"  {f!r} → {t!r}" for f, t in sorted(missing))
        )

    def test_all_step_writers_are_in_table(self):
        """등록된 모든 writer 전이가 FSM 전이표에 있어야 한다.

        표에 없는 전이를 writer가 실행하면 FSM ValueError 크래시 발생.
        """
        invalid = []
        for (from_step, to_step) in self.KNOWN_STEP_WRITERS:
            allowed = VALID_TRANSITIONS.get(from_step, [])
            if to_step not in allowed:
                invalid.append((from_step, to_step))
        assert not invalid, (
            "다음 writer 전이가 FSM 표에 없습니다 — VALID_TRANSITIONS에 추가하세요:\n"
            + "\n".join(f"  {f!r} → {t!r}" for f, t in sorted(invalid))
        )

    def test_all_parallel_transitions_have_writers(self):
        """병렬 FSM 전이표의 모든 (from, to) 쌍에 writer가 등록되어 있어야 한다."""
        missing = []
        for from_st, allowed in VALID_PARALLEL_TRANSITIONS.items():
            for to_st in allowed:
                if (from_st, to_st) not in self.KNOWN_PARALLEL_WRITERS:
                    missing.append((from_st, to_st))
        assert not missing, (
            "다음 병렬 전이에 writer가 등록되지 않았습니다 — KNOWN_PARALLEL_WRITERS에 추가하세요:\n"
            + "\n".join(f"  {f!r} → {t!r}" for f, t in sorted(missing))
        )

    def test_all_parallel_writers_are_in_table(self):
        """등록된 모든 병렬 writer 전이가 병렬 FSM 표에 있어야 한다."""
        invalid = []
        for (from_st, to_st) in self.KNOWN_PARALLEL_WRITERS:
            allowed = VALID_PARALLEL_TRANSITIONS.get(from_st, [])
            if to_st not in allowed:
                invalid.append((from_st, to_st))
        assert not invalid, (
            "다음 병렬 writer 전이가 FSM 표에 없습니다 — VALID_PARALLEL_TRANSITIONS에 추가하세요:\n"
            + "\n".join(f"  {f!r} → {t!r}" for f, t in sorted(invalid))
        )
