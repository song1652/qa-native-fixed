"""
테스트: scripts/_pipeline_registry.py (P34)

커버 대상:
  Step / ParallelStatus  — 상수 값 정확성
  PIPELINE_STEP_DEFS     — 메타데이터 완결성 (모든 Step 커버, 중복 없음)
  VALID_TRANSITIONS      — 단일 파이프라인 FSM 완결성 + _constants.py 동기화
  VALID_PARALLEL_TRANSITIONS — 병렬 FSM 완결성 + _constants.py 동기화
  assert_valid_transition / assert_valid_parallel_transition — 검증 함수
  get_step_label / get_step_script / is_terminal_step        — 조회 헬퍼
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from _pipeline_registry import (
    Step,
    ParallelStatus,
    PIPELINE_STEP_DEFS,
    STEP_DEF_BY_NAME,
    VALID_TRANSITIONS,
    VALID_PARALLEL_TRANSITIONS,
    assert_valid_transition,
    assert_valid_parallel_transition,
    get_step_label,
    get_step_script,
    is_terminal_step,
    all_step_names,
    all_parallel_status_names,
)
from _constants import (
    VALID_TRANSITIONS as CONST_TRANSITIONS,
    VALID_PARALLEL_TRANSITIONS as CONST_PARALLEL_TRANSITIONS,
)


# ─── Step 상수 ────────────────────────────────────────────────────────────────


class TestStepConstants:
    """Step 클래스 상수 값이 _constants.py의 FSM 키와 일치하는지 확인."""

    def test_all_step_values_are_strings(self):
        for attr in vars(Step):
            if not attr.startswith("_"):
                assert isinstance(getattr(Step, attr), str)

    def test_step_values_match_fsm_keys(self):
        """VALID_TRANSITIONS의 모든 키가 Step 상수로 정의되어 있음."""
        step_values = {v for k, v in vars(Step).items() if not k.startswith("_")}
        for key in VALID_TRANSITIONS:
            assert key in step_values, f"Step 상수 누락: '{key}'"

    def test_no_duplicate_step_values(self):
        """Step 상수 값 중복 없음."""
        values = [v for k, v in vars(Step).items() if not k.startswith("_")]
        assert len(values) == len(set(values)), "Step 상수 값 중복"

    def test_known_step_values(self):
        """핵심 step 이름이 예상한 문자열인지 확인."""
        assert Step.INIT == "init"
        assert Step.ANALYZED == "analyzed"
        assert Step.GENERATED == "generated"
        assert Step.DONE == "done"
        assert Step.HEAL_NEEDED == "heal_needed"
        assert Step.HEAL_FAILED == "heal_failed"
        assert Step.TIMEOUT == "timeout"


class TestParallelStatusConstants:
    """ParallelStatus 상수 값 정확성."""

    def test_all_values_are_strings(self):
        for attr in vars(ParallelStatus):
            if not attr.startswith("_"):
                assert isinstance(getattr(ParallelStatus, attr), str)

    def test_known_status_values(self):
        assert ParallelStatus.TESTING == "testing"
        assert ParallelStatus.DONE == "done"
        assert ParallelStatus.HEAL_NEEDED == "heal_needed"
        assert ParallelStatus.HEAL_FAILED == "heal_failed"
        assert ParallelStatus.EMPTY == ""

    def test_no_duplicate_status_values(self):
        """EMPTY("")를 포함해 중복 없음."""
        values = [v for k, v in vars(ParallelStatus).items() if not k.startswith("_")]
        assert len(values) == len(set(values)), "ParallelStatus 상수 값 중복"


# ─── PIPELINE_STEP_DEFS 메타데이터 ───────────────────────────────────────────


class TestPipelineStepDefs:
    """PIPELINE_STEP_DEFS 완결성 검증."""

    def test_no_duplicate_step_names(self):
        names = [s.step for s in PIPELINE_STEP_DEFS]
        assert len(names) == len(set(names)), "PIPELINE_STEP_DEFS에 중복 step 이름"

    def test_all_fsm_steps_have_def(self):
        """VALID_TRANSITIONS의 모든 step + 전이 대상이 정의되어 있음."""
        all_steps = set()
        for src, targets in VALID_TRANSITIONS.items():
            all_steps.add(src)
            all_steps.update(targets)
        for step in all_steps:
            assert step in STEP_DEF_BY_NAME, f"레지스트리에 step 정의 없음: '{step}'"

    def test_all_defs_have_nonempty_label(self):
        for defn in PIPELINE_STEP_DEFS:
            assert defn.label, f"step '{defn.step}'의 label이 비어 있음"

    def test_script_paths_use_forward_slash(self):
        """script 경로는 PROJECT_ROOT 기준 상대경로이며 백슬래시 없음."""
        for defn in PIPELINE_STEP_DEFS:
            if defn.script:
                assert "\\" not in defn.script, f"백슬래시 사용 금지: {defn.script}"

    def test_terminal_steps_have_no_script_or_are_expected(self):
        """종료 단계(is_terminal=True)는 스크립트가 없거나 실행 후 파이프라인이 끝남."""
        terminal = [d for d in PIPELINE_STEP_DEFS if d.is_terminal]
        assert len(terminal) >= 1, "종료 단계가 하나도 없음"
        terminal_names = {d.step for d in terminal}
        # DONE, HEAL_FAILED, TIMEOUT은 종료 단계여야 함
        for expected in (Step.DONE, Step.HEAL_FAILED, Step.TIMEOUT):
            assert expected in terminal_names, f"'{expected}'이 종료 단계로 표시되지 않음"

    def test_step_def_by_name_consistent_with_list(self):
        """STEP_DEF_BY_NAME과 PIPELINE_STEP_DEFS가 동일한 데이터를 가리킴."""
        for defn in PIPELINE_STEP_DEFS:
            assert STEP_DEF_BY_NAME[defn.step] is defn


# ─── VALID_TRANSITIONS (단일) ────────────────────────────────────────────────


class TestValidTransitions:
    """단일 파이프라인 FSM 전이표 완결성 + _constants.py 동기화."""

    def test_matches_constants_py(self):
        """레지스트리 표와 _constants.py 표가 완전히 일치."""
        assert VALID_TRANSITIONS == CONST_TRANSITIONS, (
            "레지스트리와 _constants.py의 VALID_TRANSITIONS가 다름 — P35 완료 전까지 동기화 필요"
        )

    def test_no_empty_allowed_list(self):
        """전이 대상 목록이 비어 있는 step 없음."""
        for step, allowed in VALID_TRANSITIONS.items():
            assert allowed, f"step '{step}'의 허용 전이 목록이 비어 있음"

    def test_all_targets_are_known_steps(self):
        """전이 대상이 모두 레지스트리에 정의된 step."""
        all_defined = set(STEP_DEF_BY_NAME.keys())
        for src, targets in VALID_TRANSITIONS.items():
            for tgt in targets:
                assert tgt in all_defined, f"알 수 없는 전이 대상: '{src}' → '{tgt}'"

    def test_init_leads_to_analyzed(self):
        assert Step.ANALYZED in VALID_TRANSITIONS[Step.INIT]

    def test_heal_needed_can_reach_done(self):
        assert Step.DONE in VALID_TRANSITIONS[Step.HEAL_NEEDED]

    def test_done_is_not_a_dead_end(self):
        """done에서 재실행(heal_needed, analyzed, init)으로 이어질 수 있음."""
        assert Step.HEAL_NEEDED in VALID_TRANSITIONS[Step.DONE]
        assert Step.ANALYZED in VALID_TRANSITIONS[Step.DONE]


# ─── VALID_PARALLEL_TRANSITIONS (병렬) ───────────────────────────────────────


class TestValidParallelTransitions:
    """병렬 파이프라인 FSM 전이표 완결성 + _constants.py 동기화."""

    def test_matches_constants_py(self):
        """레지스트리 표와 _constants.py 표가 완전히 일치."""
        assert VALID_PARALLEL_TRANSITIONS == CONST_PARALLEL_TRANSITIONS, (
            "레지스트리와 _constants.py의 VALID_PARALLEL_TRANSITIONS가 다름"
        )

    def test_empty_string_key_present(self):
        """빈 문자열 키(초기 상태)가 존재."""
        assert ParallelStatus.EMPTY in VALID_PARALLEL_TRANSITIONS

    def test_testing_leads_to_done_or_heal(self):
        allowed = VALID_PARALLEL_TRANSITIONS[ParallelStatus.TESTING]
        assert ParallelStatus.DONE in allowed
        assert ParallelStatus.HEAL_NEEDED in allowed

    def test_no_empty_allowed_list(self):
        for status, allowed in VALID_PARALLEL_TRANSITIONS.items():
            assert allowed, f"status '{status}'의 허용 전이 목록이 비어 있음"


# ─── assert_valid_transition ─────────────────────────────────────────────────


class TestAssertValidTransition:
    """단일 파이프라인 전이 검증 함수."""

    def test_valid_transition_no_exception(self):
        assert_valid_transition(Step.INIT, Step.ANALYZED)  # 예외 없음

    def test_invalid_transition_raises_value_error(self):
        with pytest.raises(ValueError, match="잘못된 step 전이"):
            assert_valid_transition(Step.INIT, Step.DONE)  # init → done 불허

    def test_unknown_current_step_passes(self):
        """알 수 없는 step은 검증 건너뜀 (하위 호환)."""
        assert_valid_transition("unknown_step", Step.DONE)  # 예외 없음

    def test_heal_needed_to_done_valid(self):
        assert_valid_transition(Step.HEAL_NEEDED, Step.DONE)

    def test_heal_needed_to_analyzed_invalid(self):
        """heal_needed → analyzed는 허용되지 않음."""
        with pytest.raises(ValueError):
            assert_valid_transition(Step.HEAL_NEEDED, Step.ANALYZED)

    def test_error_message_includes_allowed_list(self):
        with pytest.raises(ValueError) as exc:
            assert_valid_transition(Step.GENERATED, Step.INIT)
        assert "허용" in str(exc.value)

    def test_consistent_with_constants_py(self):
        """레지스트리 검증 함수와 _constants.py 검증 함수의 동작이 동일."""
        from _constants import assert_valid_transition as const_avt
        test_cases = [
            (Step.INIT, Step.ANALYZED, False),
            (Step.INIT, Step.DONE, True),   # should raise
            (Step.HEAL_NEEDED, Step.DONE, False),
        ]
        for current, next_step, should_raise in test_cases:
            registry_raised = False
            const_raised = False
            try:
                assert_valid_transition(current, next_step)
            except ValueError:
                registry_raised = True
            try:
                const_avt(current, next_step)
            except ValueError:
                const_raised = True
            assert registry_raised == const_raised, (
                f"동작 불일치: {current} → {next_step}"
            )


# ─── assert_valid_parallel_transition ────────────────────────────────────────


class TestAssertValidParallelTransition:
    """병렬 파이프라인 전이 검증 함수."""

    def test_valid_transition_no_exception(self):
        assert_valid_parallel_transition(ParallelStatus.TESTING, ParallelStatus.DONE)

    def test_invalid_transition_raises(self):
        with pytest.raises(ValueError, match="잘못된 parallel status"):
            assert_valid_parallel_transition(ParallelStatus.TESTING, ParallelStatus.ANALYZING)

    def test_unknown_status_passes(self):
        assert_valid_parallel_transition("unknown_status", ParallelStatus.DONE)

    def test_consistent_with_constants_py(self):
        from _constants import assert_valid_parallel_transition as const_avpt
        test_cases = [
            (ParallelStatus.TESTING, ParallelStatus.DONE, False),
            (ParallelStatus.TESTING, ParallelStatus.ANALYZING, True),
        ]
        for current, next_s, should_raise in test_cases:
            r_raised = c_raised = False
            try:
                assert_valid_parallel_transition(current, next_s)
            except ValueError:
                r_raised = True
            try:
                const_avpt(current, next_s)
            except ValueError:
                c_raised = True
            assert r_raised == c_raised, f"동작 불일치: {current} → {next_s}"


# ─── 조회 헬퍼 ───────────────────────────────────────────────────────────────


class TestHelpers:
    """get_step_label / get_step_script / is_terminal_step / all_step_names."""

    def test_get_step_label_known(self):
        assert get_step_label(Step.DONE) == "실행 완료"
        assert get_step_label(Step.HEAL_NEEDED) == "힐링 필요"
        assert get_step_label(Step.ANALYZED) == "DOM 분석"

    def test_get_step_label_unknown_returns_step(self):
        assert get_step_label("mystery_step") == "mystery_step"

    def test_get_step_script_known(self):
        assert get_step_script(Step.ANALYZED) == "scripts/01_analyze.py"
        assert get_step_script(Step.GENERATED) == "scripts/02_generate.py"

    def test_get_step_script_none_for_no_script(self):
        assert get_step_script(Step.INIT) is None
        assert get_step_script(Step.HEAL_FAILED) is None

    def test_get_step_script_unknown_returns_none(self):
        assert get_step_script("not_a_step") is None

    def test_is_terminal_step_true(self):
        assert is_terminal_step(Step.DONE) is True
        assert is_terminal_step(Step.HEAL_FAILED) is True
        assert is_terminal_step(Step.TIMEOUT) is True

    def test_is_terminal_step_false(self):
        assert is_terminal_step(Step.INIT) is False
        assert is_terminal_step(Step.ANALYZED) is False
        assert is_terminal_step(Step.HEAL_NEEDED) is False

    def test_is_terminal_step_unknown_returns_false(self):
        assert is_terminal_step("no_such_step") is False

    def test_all_step_names_contains_all_steps(self):
        names = all_step_names()
        for attr in vars(Step):
            if not attr.startswith("_"):
                assert getattr(Step, attr) in names

    def test_all_step_names_no_duplicates(self):
        names = all_step_names()
        assert len(names) == len(set(names))

    def test_all_parallel_status_names_includes_empty(self):
        assert "" in all_parallel_status_names()
