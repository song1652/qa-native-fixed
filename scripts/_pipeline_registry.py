"""
파이프라인 레지스트리 (P34) — 단계 이름·전이 규칙·스크립트·라벨의 단일 소스.

현황 문제
---------
- step 이름("analyzed", "heal_needed" 등)이 15개 파일에 문자열 리터럴로 흩어져 있음
- FSM 전이 표가 _constants.py에 dict 리터럴 두 개로 존재
- 새 단계를 추가하려면 12~14곳을 직접 수정해야 함

해결 방향
---------
이 모듈을 단일 소스로 삼아:
  - 단계 이름은 Step / ParallelStatus 상수 클래스에서 참조
  - 단계 메타데이터(스크립트·라벨·종료 여부)는 PipelineStepDef 목록에서 선언
  - FSM 전이 규칙은 위 상수를 사용해 선언 → 오탈자 방지

마이그레이션 단계
-----------------
P34 (현재): 이 모듈 신규 생성 + 테스트. 기존 _constants.py는 건드리지 않음.
P35       : _constants.py 의 VALID_TRANSITIONS / VALID_PARALLEL_TRANSITIONS 를
            이 모듈에서 파생하도록 전환 (assert_valid_* 계약 유지).
P36       : 99_merge.py status 파생 로직 → 이 모듈 참조로 교체.
P37       : serve.py FSM 검증 → 이 모듈 직접 호출.
P38       : 문서 단계 목록 자동 갱신 or 어긋남 감지 테스트.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ── 상수 ────────────────────────────────────────────────────────────────────


class Step:
    """단일 파이프라인 step 이름 상수 (pipeline.json의 'step' 필드값).

    문자열 리터럴 대신 이 상수를 사용하면 오탈자가 런타임이 아닌 임포트 시점에
    NameError로 드러나고, IDE 자동완성·리팩터링 도구가 추적할 수 있다.
    """
    INIT        = "init"
    ANALYZED    = "analyzed"
    PLANNED     = "planned"       # 심의 Agent가 plan 저장 시 경유하는 선택적 중간 단계
    GENERATED   = "generated"
    REVIEWED    = "reviewed"
    DONE        = "done"
    HEAL_NEEDED = "heal_needed"
    HEAL_FAILED = "heal_failed"
    TIMEOUT     = "timeout"


class ParallelStatus:
    """병렬 파이프라인 status 이름 상수 (parallel.json / quick.json의 'status' 필드값).

    단일 파이프라인 Step과 이름이 겹치는 값(done, heal_needed 등)이 있지만,
    필드명(step vs status)과 파일(pipeline.json vs parallel.json)이 다르다.
    """
    EMPTY       = ""              # 초기 — 파일이 없거나 status가 아직 설정되지 않음
    INIT        = "init"
    ANALYZING   = "analyzing"
    READY       = "ready"
    ERROR       = "error"
    TESTING     = "testing"
    DONE        = "done"
    HEAL_NEEDED = "heal_needed"
    HEAL_FAILED = "heal_failed"


# ── 단계 메타데이터 ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PipelineStepDef:
    """단일 파이프라인 단계 하나의 선언적 메타데이터.

    Attributes:
        step        Step 상수값 (pipeline.json 'step' 필드에 기록되는 문자열)
        label       UI / 리포트 표시 라벨 (한국어)
        script      실행 스크립트 상대경로 (PROJECT_ROOT 기준). 없으면 None.
        is_terminal True이면 정상/비정상 종료 단계 — 후속 스크립트가 없음.
    """
    step: str
    label: str
    script: Optional[str] = None
    is_terminal: bool = False


# 실행 순서를 반영한 선언 목록 (정렬 기준은 논리 순서 — FSM과 독립)
PIPELINE_STEP_DEFS: list[PipelineStepDef] = [
    PipelineStepDef(
        step=Step.INIT,
        label="초기화",
        script=None,
        is_terminal=False,
    ),
    PipelineStepDef(
        step=Step.ANALYZED,
        label="DOM 분석",
        script="scripts/01_analyze.py",
        is_terminal=False,
    ),
    PipelineStepDef(
        step=Step.PLANNED,
        label="심의 (계획)",
        script="scripts/02a_dialog.py",
        is_terminal=False,
    ),
    PipelineStepDef(
        step=Step.GENERATED,
        label="코드 생성",
        script="scripts/02_generate.py",
        is_terminal=False,
    ),
    PipelineStepDef(
        step=Step.REVIEWED,
        label="린트 검토",
        script="scripts/03_lint.py",
        is_terminal=False,
    ),
    PipelineStepDef(
        step=Step.DONE,
        label="실행 완료",
        script="scripts/05_execute.py",
        is_terminal=True,
    ),
    PipelineStepDef(
        step=Step.HEAL_NEEDED,
        label="힐링 필요",
        script="scripts/06_heal.py",
        is_terminal=False,
    ),
    PipelineStepDef(
        step=Step.HEAL_FAILED,
        label="힐링 초과",
        script=None,
        is_terminal=True,
    ),
    PipelineStepDef(
        step=Step.TIMEOUT,
        label="타임아웃",
        script=None,
        is_terminal=True,
    ),
]

# 이름 → 메타데이터 조회 딕셔너리 (O(1) 접근)
STEP_DEF_BY_NAME: dict[str, PipelineStepDef] = {
    s.step: s for s in PIPELINE_STEP_DEFS
}


# ── FSM 전이 규칙 (단일 파이프라인) ─────────────────────────────────────────
# Step 상수를 키로 사용 → 오탈자 방지 + IDE 추적 가능

VALID_TRANSITIONS: dict[str, list[str]] = {
    Step.INIT:        [Step.ANALYZED],
    Step.ANALYZED:    [Step.PLANNED, Step.GENERATED],   # planned: 선택적 중간 단계
    Step.PLANNED:     [Step.GENERATED],
    Step.GENERATED:   [Step.REVIEWED],
    Step.REVIEWED:    [Step.DONE, Step.HEAL_NEEDED, Step.TIMEOUT],
    Step.DONE:        [Step.HEAL_NEEDED, Step.ANALYZED, Step.INIT],  # init: 재실행 전체 리셋
    Step.HEAL_NEEDED: [Step.DONE, Step.HEAL_FAILED, Step.TIMEOUT],
    Step.HEAL_FAILED: [Step.ANALYZED, Step.INIT],
    Step.TIMEOUT:     [Step.DONE, Step.HEAL_NEEDED, Step.INIT],
}


# ── FSM 전이 규칙 (병렬 파이프라인) ─────────────────────────────────────────
# ParallelStatus 상수를 키로 사용

VALID_PARALLEL_TRANSITIONS: dict[str, list[str]] = {
    # EMPTY: 초기 상태. _validate_transition_locked_raw가 falsy current_val이면
    # 검증을 건너뛰지만, assert_valid_parallel_transition() 직접 호출 시에는
    # 이 표가 계약이므로 항목을 유지한다 (fail-closed 보장).
    ParallelStatus.EMPTY:       [ParallelStatus.INIT, ParallelStatus.TESTING],
    ParallelStatus.INIT:        [ParallelStatus.ANALYZING, ParallelStatus.TESTING],
    ParallelStatus.ANALYZING:   [ParallelStatus.READY, ParallelStatus.ERROR],
    ParallelStatus.READY:       [ParallelStatus.TESTING],
    ParallelStatus.ERROR:       [ParallelStatus.INIT, ParallelStatus.TESTING],
    ParallelStatus.TESTING:     [ParallelStatus.DONE, ParallelStatus.HEAL_NEEDED,
                                 ParallelStatus.HEAL_FAILED],
    ParallelStatus.DONE:        [ParallelStatus.TESTING, ParallelStatus.INIT],
    ParallelStatus.HEAL_NEEDED: [ParallelStatus.DONE, ParallelStatus.HEAL_FAILED,
                                 ParallelStatus.TESTING],
    ParallelStatus.HEAL_FAILED: [ParallelStatus.TESTING, ParallelStatus.INIT],
}


# ── 검증 함수 ────────────────────────────────────────────────────────────────


def assert_valid_transition(current: str, next_step: str) -> None:
    """단일 파이프라인 step 전이가 허용되는지 검증. 잘못된 전이 시 ValueError.

    _constants.py의 동명 함수와 계약이 동일하다. P35에서 _constants.py가
    이 함수를 re-export하도록 전환되면 두 구현이 하나로 통합된다.
    """
    allowed = VALID_TRANSITIONS.get(current)
    if allowed is None:
        return  # 알 수 없는 step → 건너뜀 (하위 호환)
    if next_step not in allowed:
        raise ValueError(
            f"잘못된 step 전이: '{current}' → '{next_step}'. "
            f"허용: {allowed}. "
            f"파이프라인 단계가 건너뛰어졌을 수 있습니다. "
            f"state/pipeline.json을 확인하세요."
        )


def assert_valid_parallel_transition(current: str, next_status: str) -> None:
    """병렬 파이프라인 status 전이가 허용되는지 검증. 잘못된 전이 시 ValueError.

    _constants.py의 동명 함수와 계약이 동일하다.
    """
    allowed = VALID_PARALLEL_TRANSITIONS.get(current)
    if allowed is None:
        return  # 알 수 없는 status → 건너뜀 (하위 호환)
    if next_status not in allowed:
        raise ValueError(
            f"잘못된 parallel status 전이: '{current}' → '{next_status}'. "
            f"허용: {allowed}. "
            f"state/parallel.json 또는 state/quick.json을 확인하세요."
        )


# ── 조회 헬퍼 ────────────────────────────────────────────────────────────────


def get_step_label(step: str) -> str:
    """step 이름 → UI 표시 라벨. 알 수 없는 step이면 step 이름 그대로 반환."""
    defn = STEP_DEF_BY_NAME.get(step)
    return defn.label if defn else step


def get_step_script(step: str) -> Optional[str]:
    """step 이름 → 실행 스크립트 상대경로 (없거나 알 수 없으면 None)."""
    defn = STEP_DEF_BY_NAME.get(step)
    return defn.script if defn else None


def is_terminal_step(step: str) -> bool:
    """step이 종료 단계인지 반환 (알 수 없으면 False)."""
    defn = STEP_DEF_BY_NAME.get(step)
    return defn.is_terminal if defn else False


def all_step_names() -> list[str]:
    """등록된 모든 단일 파이프라인 step 이름 목록 (선언 순서)."""
    return [s.step for s in PIPELINE_STEP_DEFS]


def all_parallel_status_names() -> list[str]:
    """등록된 모든 병렬 파이프라인 status 이름 목록."""
    return list(VALID_PARALLEL_TRANSITIONS.keys())
