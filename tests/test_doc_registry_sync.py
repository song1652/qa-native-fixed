"""
테스트: 문서와 _pipeline_registry.py 레지스트리 동기화 검증 (P38)

레지스트리에 새 step/status를 추가했는데 문서가 갱신되지 않으면 이 테스트가 실패한다.
"됐을 것 같다" 방지 — 문서 수정 없이 레지스트리만 바꾸면 CI가 잡아낸다.

대상 문서:
  doc/PIPELINE_STATE.md — step/status 열거 + 전이 규칙 참조
  doc/SCRIPTS_GUIDE.md  — 스크립트별 단계 언급
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from _pipeline_registry import (
    Step,
    ParallelStatus,
    VALID_TRANSITIONS,
    VALID_PARALLEL_TRANSITIONS,
    all_step_names,
    all_parallel_status_names,
)

_REPO_ROOT = Path(__file__).parent.parent
PIPELINE_STATE_MD = _REPO_ROOT / "doc" / "PIPELINE_STATE.md"
SCRIPTS_GUIDE_MD  = _REPO_ROOT / "doc" / "SCRIPTS_GUIDE.md"


# ── PIPELINE_STATE.md ────────────────────────────────────────────────────────


class TestPipelineStateMdSync:
    """doc/PIPELINE_STATE.md 가 레지스트리의 모든 step/status를 언급하는지 확인."""

    @pytest.fixture(scope="class")
    def doc_text(self):
        assert PIPELINE_STATE_MD.exists(), f"문서 없음: {PIPELINE_STATE_MD}"
        return PIPELINE_STATE_MD.read_text(encoding="utf-8")

    # ── 단일 파이프라인 Step ──────────────────────────────────────────

    @pytest.mark.parametrize("step", [
        Step.INIT, Step.ANALYZED, Step.PLANNED, Step.GENERATED,
        Step.REVIEWED, Step.DONE, Step.HEAL_NEEDED, Step.HEAL_FAILED,
        Step.TIMEOUT,
    ])
    def test_single_step_mentioned_in_doc(self, doc_text, step):
        """모든 단일 파이프라인 step 이름이 PIPELINE_STATE.md에 등장해야 함."""
        assert step in doc_text, (
            f"step '{step}'가 {PIPELINE_STATE_MD.name}에 없음. "
            f"레지스트리에 step을 추가/변경했다면 문서도 갱신하세요."
        )

    def test_no_unknown_steps_in_doc_step_line(self, doc_text):
        """파이프라인 pipeline.json 스키마 섹션의 step 열거에 레지스트리에 없는 값이 없는지 확인.

        열거 라인 예: "step": "init | analyzed | planned | ..."
        단, discuss.json 섹션(팀 토론용 FSM)은 다른 상태 머신이므로 제외.
        """
        known = set(all_step_names())
        # discuss.json 섹션 이전(파이프라인 스키마 섹션)만 검사
        # discuss.json에는 "approved|rejected" 같은 토론 전용 step이 있어 제외
        pipeline_section = doc_text.split("## state/discuss.json")[0]
        for line in pipeline_section.splitlines():
            if '"step":' in line and "|" in line:
                # 파이프로 구분된 step 이름 추출
                parts = line.split('"')[3] if line.count('"') >= 4 else ""
                for token in parts.split("|"):
                    name = token.strip()
                    if name:
                        assert name in known, (
                            f"문서 pipeline.json step 열거에 알 수 없는 값: '{name}' "
                            f"(레지스트리에 없음). 문서와 레지스트리를 동기화하세요."
                        )

    # ── 병렬 파이프라인 ParallelStatus ────────────────────────────────

    @pytest.mark.parametrize("status", [
        # EMPTY("")는 문서에서 '""' 형태로 표현되므로 별도 검사
        ParallelStatus.INIT, ParallelStatus.ANALYZING, ParallelStatus.READY,
        ParallelStatus.ERROR, ParallelStatus.TESTING, ParallelStatus.DONE,
        ParallelStatus.HEAL_NEEDED, ParallelStatus.HEAL_FAILED,
    ])
    def test_parallel_status_mentioned_in_doc(self, doc_text, status):
        """모든 병렬 파이프라인 status가 PIPELINE_STATE.md에 등장해야 함."""
        assert status in doc_text, (
            f"status '{status}'가 {PIPELINE_STATE_MD.name}에 없음. "
            f"레지스트리에 status를 추가/변경했다면 문서도 갱신하세요."
        )

    def test_parallel_empty_status_represented_in_doc(self, doc_text):
        """ParallelStatus.EMPTY (\"\")는 문서에서 '\"\"' 형태로 표현됨."""
        assert '""' in doc_text, (
            f"ParallelStatus.EMPTY(\"\")가 {PIPELINE_STATE_MD.name}에 표현되지 않음."
        )

    def test_registry_reference_updated_from_constants(self, doc_text):
        """P35 이후 문서 참조가 _constants.py → _pipeline_registry.py로 갱신됐는지 확인."""
        assert "_pipeline_registry.py" in doc_text, (
            "doc/PIPELINE_STATE.md가 여전히 _constants.py를 참조하고 있음. "
            "_pipeline_registry.py로 갱신하세요 (P35 참조)."
        )

    # ── FSM 전이 규칙 완결성 ─────────────────────────────────────────

    def test_all_fsm_source_steps_in_doc(self, doc_text):
        """VALID_TRANSITIONS의 모든 소스 step이 문서에 등장."""
        for step in VALID_TRANSITIONS:
            assert step in doc_text, (
                f"FSM 소스 step '{step}'가 {PIPELINE_STATE_MD.name}에 없음."
            )

    def test_all_parallel_fsm_source_statuses_in_doc(self, doc_text):
        """VALID_PARALLEL_TRANSITIONS의 비어있지 않은 소스 status가 문서에 등장."""
        for status in VALID_PARALLEL_TRANSITIONS:
            if not status:          # EMPTY("") → 별도 테스트에서 검증
                continue
            assert status in doc_text, (
                f"병렬 FSM 소스 status '{status}'가 {PIPELINE_STATE_MD.name}에 없음."
            )


# ── SCRIPTS_GUIDE.md ────────────────────────────────────────────────────────


class TestScriptsGuideMdSync:
    """doc/SCRIPTS_GUIDE.md 가 핵심 실행 스크립트 단계를 언급하는지 확인."""

    @pytest.fixture(scope="class")
    def doc_text(self):
        if not SCRIPTS_GUIDE_MD.exists():
            pytest.skip(f"문서 없음: {SCRIPTS_GUIDE_MD}")
        return SCRIPTS_GUIDE_MD.read_text(encoding="utf-8")

    @pytest.mark.parametrize("script", [
        "01_analyze.py",
        "02_generate.py",
        "05_execute.py",
        "06_heal.py",
    ])
    def test_core_scripts_mentioned(self, doc_text, script):
        """핵심 파이프라인 스크립트 파일명이 SCRIPTS_GUIDE.md에 등장."""
        assert script in doc_text, (
            f"스크립트 '{script}'가 {SCRIPTS_GUIDE_MD.name}에 없음. "
            f"새 스크립트를 추가했다면 문서도 갱신하세요."
        )

    def test_registry_scripts_exist_on_disk(self):
        """레지스트리에 등록된 script 경로가 실제 파일로 존재하는지 확인.

        script 경로를 바꿨거나 파일을 삭제했는데 레지스트리를 업데이트하지
        않은 경우를 잡아낸다.
        """
        from _pipeline_registry import PIPELINE_STEP_DEFS
        missing = []
        for defn in PIPELINE_STEP_DEFS:
            if defn.script:
                full = _REPO_ROOT / defn.script
                if not full.exists():
                    missing.append(f"{defn.step}: {defn.script}")
        assert not missing, (
            "레지스트리에 등록된 스크립트가 디스크에 없음:\n"
            + "\n".join(f"  - {m}" for m in missing)
        )
