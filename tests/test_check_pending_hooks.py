"""
check_pending_*.py 훅 스크립트 + hook_utils.remaining_steps_hint 테스트 (P44).

검증 범위:
  - remaining_steps_hint(): 레지스트리 기반 잔여 단계 목록 생성
  - check_pending 4개 스크립트의 트리거 조건이 레지스트리 상수를 사용
  - 트리거 값이 Step.* / ParallelStatus.* 상수와 일치
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
for _p in (str(_SCRIPTS),):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── remaining_steps_hint 단위 테스트 ─────────────────────────────────────────

class TestRemainingStepsHint:
    """hook_utils.remaining_steps_hint() 검증."""

    def test_from_init_returns_non_empty(self):
        from _pipeline_registry import Step
        from hook_utils import remaining_steps_hint
        hints = remaining_steps_hint(Step.INIT)
        assert len(hints) > 0

    def test_from_init_starts_with_analyze(self):
        from _pipeline_registry import Step
        from hook_utils import remaining_steps_hint
        hints = remaining_steps_hint(Step.INIT)
        assert any("01_analyze" in h for h in hints), (
            f"01_analyze.py가 첫 번째 힌트에 없음: {hints}"
        )

    def test_from_reviewed_starts_with_execute(self):
        """Step.REVIEWED 이후: 05_execute.py(done)와 06_heal.py(heal_needed) 포함."""
        from _pipeline_registry import Step
        from hook_utils import remaining_steps_hint
        hints = remaining_steps_hint(Step.REVIEWED)
        assert hints, "Step.REVIEWED 이후 힌트가 비어있음"
        # Step.DONE은 is_terminal=True이지만 05_execute.py 스크립트가 있으므로 포함
        assert any("05_execute" in h for h in hints), (
            f"05_execute.py(done 단계 스크립트)가 힌트에 없음: {hints}"
        )

    def test_from_reviewed_does_not_include_analyze(self):
        from _pipeline_registry import Step
        from hook_utils import remaining_steps_hint
        hints = remaining_steps_hint(Step.REVIEWED)
        assert not any("01_analyze" in h for h in hints), (
            "01_analyze는 reviewed 이후 목록에 없어야 함"
        )

    def test_no_script_steps_excluded(self):
        """script=None 인 단계(heal_failed, timeout)는 목록에 없어야 함.
        is_terminal=True이어도 script가 있으면 포함 (Step.DONE → 05_execute.py)."""
        from _pipeline_registry import Step
        from hook_utils import remaining_steps_hint
        hints = remaining_steps_hint(Step.INIT)
        # heal_failed/timeout은 script=None → 자동 제외
        assert not any("heal_failed" in h for h in hints)
        assert not any("timeout" in h for h in hints)
        # Step.DONE은 terminal이지만 05_execute.py 스크립트가 있으므로 포함됨
        assert any("05_execute" in h for h in hints)

    def test_from_heal_needed_returns_sub_steps(self):
        """P57: heal_needed 이후 06_auto_heal / 06a_dialog 서브 단계가 반환됨.

        06_heal.py(첫 HEAL_NEEDED 항목) 다음에 등록된 06_auto_heal.py / 06a_dialog.py가
        remaining_steps_hint에 포함되어야 한다. heal_failed/timeout은 script=None이므로 제외.
        """
        from _pipeline_registry import Step
        from hook_utils import remaining_steps_hint
        hints = remaining_steps_hint(Step.HEAL_NEEDED)
        # 서브 단계가 포함돼야 함
        assert any("06_auto_heal" in h for h in hints), f"06_auto_heal 힌트 없음: {hints}"
        assert any("06a_dialog" in h for h in hints), f"06a_dialog 힌트 없음: {hints}"
        # heal_failed/timeout은 script=None → 제외
        assert not any("heal_failed" in h for h in hints)
        assert not any("timeout" in h for h in hints)

    def test_unknown_step_returns_empty(self):
        from hook_utils import remaining_steps_hint
        hints = remaining_steps_hint("nonexistent_step")
        assert hints == []

    def test_hint_format_contains_python_and_script(self):
        from _pipeline_registry import Step
        from hook_utils import remaining_steps_hint
        hints = remaining_steps_hint(Step.INIT)
        for h in hints:
            assert h.startswith(tuple("123456789")), f"번호로 시작해야 함: {h!r}"
            assert "python" in h, f"'python' 포함 필요: {h!r}"
            assert ".py" in h, f"'.py' 포함 필요: {h!r}"

    def test_hint_numbering_is_sequential(self):
        from _pipeline_registry import Step
        from hook_utils import remaining_steps_hint
        hints = remaining_steps_hint(Step.INIT)
        for i, h in enumerate(hints, 1):
            assert h.startswith(f"{i}."), f"힌트 {i}번 번호 불일치: {h!r}"

    def test_from_done_returns_heal_hint(self):
        """done 이후에 heal_needed(06_heal.py)가 있으므로 힌트에 포함된다."""
        from _pipeline_registry import Step
        from hook_utils import remaining_steps_hint
        hints = remaining_steps_hint(Step.DONE)
        # PIPELINE_STEP_DEFS 순서상 done 뒤에 heal_needed(06_heal.py)가 있음
        assert any("06_heal" in h for h in hints)


# ── 트리거 조건 레지스트리 상수 일치 검증 ────────────────────────────────────

class TestTriggerConditionsMatchRegistry:
    """check_pending 스크립트가 레지스트리 상수로 트리거 조건을 정의하는지 확인."""

    def test_pipeline_trigger_uses_step_init(self):
        """check_pending_pipeline.py: Step.INIT 임포트 + 사용 확인."""
        src = (_SCRIPTS / "check_pending_pipeline.py").read_text(encoding="utf-8")
        assert "from _pipeline_registry import Step" in src, (
            "Step 레지스트리 임포트 누락"
        )
        assert "Step.INIT" in src, "Step.INIT 미사용"
        # 구 하드코딩 문자열 직접 사용 여부 확인 (check_state value= 인자)
        assert 'value="init"' not in src, (
            '하드코딩된 "init" 문자열이 남아있음 — Step.INIT 사용 필요'
        )

    def test_approve_trigger_uses_step_reviewed(self):
        """check_pending_approve.py: Step.REVIEWED 임포트 + 사용 확인."""
        src = (_SCRIPTS / "check_pending_approve.py").read_text(encoding="utf-8")
        assert "from _pipeline_registry import Step" in src
        assert "Step.REVIEWED" in src
        assert 'value="reviewed"' not in src, (
            '하드코딩된 "reviewed" 문자열이 남아있음 — Step.REVIEWED 사용 필요'
        )

    def test_parallel_trigger_uses_parallelstatus_ready(self):
        """check_pending_parallel.py: ParallelStatus.READY 임포트 + 사용 확인."""
        src = (_SCRIPTS / "check_pending_parallel.py").read_text(encoding="utf-8")
        assert "from _pipeline_registry import ParallelStatus" in src
        assert "ParallelStatus.READY" in src
        assert 'value="ready"' not in src, (
            '하드코딩된 "ready" 문자열이 남아있음 — ParallelStatus.READY 사용 필요'
        )

    def test_quick_heal_trigger_uses_parallelstatus_heal_needed(self):
        """check_pending_quick_heal.py: ParallelStatus.HEAL_NEEDED 임포트 + 사용 확인."""
        src = (_SCRIPTS / "check_pending_quick_heal.py").read_text(encoding="utf-8")
        assert "from _pipeline_registry import ParallelStatus" in src
        assert "ParallelStatus.HEAL_NEEDED" in src
        assert 'value="heal_needed"' not in src, (
            '하드코딩된 "heal_needed" 문자열이 남아있음 — ParallelStatus.HEAL_NEEDED 사용 필요'
        )

    def test_trigger_values_match_actual_constants(self):
        """Step.INIT / Step.REVIEWED / ParallelStatus.READY / ParallelStatus.HEAL_NEEDED
        의 실제 값이 기존 파이프라인과 일치하는지 확인."""
        from _pipeline_registry import Step, ParallelStatus
        assert Step.INIT == "init"
        assert Step.REVIEWED == "reviewed"
        assert ParallelStatus.READY == "ready"
        assert ParallelStatus.HEAL_NEEDED == "heal_needed"

    def test_pipeline_script_uses_remaining_steps_hint(self):
        """check_pending_pipeline.py가 remaining_steps_hint를 임포트·사용."""
        src = (_SCRIPTS / "check_pending_pipeline.py").read_text(encoding="utf-8")
        assert "remaining_steps_hint" in src

    def test_approve_script_uses_remaining_steps_hint(self):
        """check_pending_approve.py가 remaining_steps_hint를 임포트·사용."""
        src = (_SCRIPTS / "check_pending_approve.py").read_text(encoding="utf-8")
        assert "remaining_steps_hint" in src


# ── remaining_steps_hint 레지스트리 일관성 ───────────────────────────────────

class TestHintRegistryConsistency:
    """레지스트리가 변경될 때 hint가 자동으로 따라가는지 확인."""

    def test_all_steps_with_script_appear_after_init(self):
        """PIPELINE_STEP_DEFS의 script 있는 단계(terminal 포함)가 모두 힌트에 등장."""
        from _pipeline_registry import PIPELINE_STEP_DEFS, Step
        from hook_utils import remaining_steps_hint
        hints_text = "\n".join(remaining_steps_hint(Step.INIT))
        expected = [
            s for s in PIPELINE_STEP_DEFS
            if s.script and s.step != Step.INIT  # init 자신은 제외
        ]
        for s in expected:
            assert s.script in hints_text, (
                f"스크립트 '{s.script}' (step={s.step})가 힌트에 없음 — "
                "PIPELINE_STEP_DEFS 추가 시 자동 반영됨"
            )
