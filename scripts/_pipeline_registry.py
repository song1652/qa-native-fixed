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
    # P57: 03a_dialog, 04_approve는 REVIEWED 상태에서 실행되는 서브 단계.
    # STEP_DEF_BY_NAME은 첫 선언이 우선(step 중복 시)이므로 canonical 항목이 먼저 와야 한다.
    PipelineStepDef(
        step=Step.REVIEWED,
        label="리뷰 심의",
        script="scripts/03a_dialog.py",
        is_terminal=False,
    ),
    PipelineStepDef(
        step=Step.REVIEWED,
        label="승인",
        script="scripts/04_approve.py",
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
    # P57: 06_auto_heal, 06a_dialog는 HEAL_NEEDED 상태에서 실행되는 서브 단계.
    PipelineStepDef(
        step=Step.HEAL_NEEDED,
        label="자동 힐링",
        script="scripts/06_auto_heal.py",
        is_terminal=False,
    ),
    PipelineStepDef(
        step=Step.HEAL_NEEDED,
        label="힐링 심의",
        script="scripts/06a_dialog.py",
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
# P57: 서브 단계(같은 step 이름)가 여럿이면 첫 번째 선언이 대표(canonical) 항목이 된다.
# 이유: get_step_label(Step.HEAL_NEEDED) → "힐링 필요" (첫 항목 06_heal.py 라벨) 유지.
# remaining_steps_hint()는 PIPELINE_STEP_DEFS 전체를 선형 탐색하므로 이 dict와 무관.
STEP_DEF_BY_NAME: dict[str, PipelineStepDef] = {}
for _s in PIPELINE_STEP_DEFS:
    if _s.step not in STEP_DEF_BY_NAME:
        STEP_DEF_BY_NAME[_s.step] = _s

# ── 구 step 호환 맵 (P58) ─────────────────────────────────────────────────────
# pipeline.json에 기록된 구버전 step 값을 현재 상수로 매핑.
# serve.py build_pipeline_registry()가 이 dict를 단일 소스로 사용한다.
STEP_COMPAT: dict[str, str] = {
    "scaffolded": Step.GENERATED,
    "linted":     Step.GENERATED,
    "approved":   Step.REVIEWED,
}

# ── 병렬 파이프라인 step 라벨 (P58) ──────────────────────────────────────────
# serve.py build_pipeline_registry()의 parallel_step_labels 단일 소스.
# "generating"은 레지스트리 미등록 UI 파생 상태 (ready + files>0 조건에서 추론).
PARALLEL_STEP_LABELS: dict[str, str] = {
    ParallelStatus.INIT:        "초기화",
    ParallelStatus.ANALYZING:   "DOM 분석",
    ParallelStatus.READY:       "코드 생성 대기",
    "generating":               "코드 생성",
    ParallelStatus.TESTING:     "테스트 실행",
    ParallelStatus.DONE:        "완료",
    ParallelStatus.HEAL_NEEDED: "힐링 필요",
    ParallelStatus.HEAL_FAILED: "힐링 초과",
    ParallelStatus.ERROR:       "오류",
}


# ── FSM 전이 규칙 (단일 파이프라인) ─────────────────────────────────────────
# Step 상수를 키로 사용 → 오탈자 방지 + IDE 추적 가능

VALID_TRANSITIONS: dict[str, list[str]] = {
    Step.INIT:        [Step.ANALYZED],
    Step.ANALYZED:    [Step.PLANNED, Step.GENERATED],  # C-1(P97): 프롬프트가 planned를 사용 — 복원
    Step.PLANNED:     [Step.GENERATED],
    Step.GENERATED:   [Step.REVIEWED],
    Step.REVIEWED:    [Step.DONE, Step.HEAL_NEEDED, Step.TIMEOUT, Step.GENERATED,
                       Step.HEAL_FAILED],  # P60: 반려→재작성 / C2: 사이트 불가 즉시 HEAL_FAILED
    Step.DONE:        [Step.HEAL_NEEDED, Step.ANALYZED, Step.INIT, Step.HEAL_FAILED,
                       Step.TIMEOUT],  # H-1(P104): 재실행 타임아웃 처리 경로
    Step.HEAL_NEEDED: [Step.DONE, Step.HEAL_FAILED, Step.TIMEOUT],
    Step.HEAL_FAILED: [Step.ANALYZED, Step.INIT,
                       Step.DONE, Step.HEAL_NEEDED,
                       Step.TIMEOUT],  # C-2(P98) + H-1(P104): 복구·타임아웃 경로
    Step.TIMEOUT:     [Step.DONE, Step.HEAL_NEEDED, Step.INIT, Step.HEAL_FAILED],  # C2: 타임아웃→힐링실패 경로
}


# ── FSM 전이 규칙 (병렬 파이프라인) ─────────────────────────────────────────
# ParallelStatus 상수를 키로 사용

VALID_PARALLEL_TRANSITIONS: dict[str, list[str]] = {
    # EMPTY: 초기 상태. _validate_transition_locked_raw가 falsy current_val이면
    # 검증을 건너뛰지만, assert_valid_parallel_transition() 직접 호출 시에는
    # 이 표가 계약이므로 항목을 유지한다 (fail-closed 보장).
    ParallelStatus.EMPTY:       [ParallelStatus.INIT, ParallelStatus.TESTING],
    ParallelStatus.INIT:        [ParallelStatus.ANALYZING, ParallelStatus.TESTING],
    ParallelStatus.ANALYZING:   [ParallelStatus.READY, ParallelStatus.TESTING, ParallelStatus.ERROR],  # P71: 재실행 경로 크래시 방지
    ParallelStatus.READY:       [ParallelStatus.TESTING],
    ParallelStatus.ERROR:       [ParallelStatus.INIT, ParallelStatus.TESTING],
    ParallelStatus.TESTING:     [ParallelStatus.DONE, ParallelStatus.HEAL_NEEDED,
                                 ParallelStatus.HEAL_FAILED, ParallelStatus.ERROR],  # C1: exit 5(수집 0건) 처리
    ParallelStatus.DONE:        [ParallelStatus.TESTING, ParallelStatus.INIT],
    ParallelStatus.HEAL_NEEDED: [ParallelStatus.DONE, ParallelStatus.HEAL_FAILED,
                                 ParallelStatus.TESTING],
    ParallelStatus.HEAL_FAILED: [ParallelStatus.TESTING, ParallelStatus.INIT],
}

# ── heal_count 리셋 정책 단일 소스 (M-4/P121) ──────────────────────────────
# 05_execute.py / 99_merge.py / serve.py가 각자 하드코딩하던 집합을 통합.
# "새 실행 시작" = 이전 사이클이 완전히 종료된 상태 (DONE/HEAL_FAILED 등).
# HEAL_NEEDED는 힐링 재실행이므로 포함하지 않음 → heal_count 누적 유지.
RESETTABLE_STEPS: frozenset = frozenset({
    Step.DONE, Step.HEAL_FAILED, Step.TIMEOUT,
})
RESETTABLE_PARALLEL_STATUSES: frozenset = frozenset({
    ParallelStatus.DONE, ParallelStatus.HEAL_FAILED,
    ParallelStatus.ERROR, ParallelStatus.INIT, ParallelStatus.EMPTY,
    ParallelStatus.TESTING,  # 크래시 후 TESTING 잔류 시 heal_count 리셋 (P110)
})


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


# ── 초기 스키마 팩토리 (P39) ─────────────────────────────────────────────────
# pipeline.json 초기값이 run_qa.py / serve.py 두 곳에 중복 선언되어 필드가 어긋남.
# 이 팩토리를 단일 소스로 삼는다.

def make_initial_pipeline_state(
    url: str = "",
    test_cases: Optional[list] = None,
    cases_path: str = "",
    group_dir: str = "",
    created_at: Optional[str] = None,
) -> dict:
    """pipeline.json 초기 상태 딕셔너리를 반환하는 팩토리 함수 (단일 소스).

    Args:
        url:        분석 대상 URL. 대시보드 리셋 시에는 빈 문자열.
        test_cases: 케이스 목록. None이면 빈 리스트로 초기화.
        cases_path: testcases/ 하위 경로. 빈 문자열이면 group_dir을 유도하지 않음.
        group_dir:  그룹 디렉터리 이름. 빈 문자열이면 cases_path에서 자동 유도.
        created_at: ISO datetime 문자열. None이면 현재 시각으로 자동 설정.

    Returns:
        pipeline.json 에 쓰기 적합한 초기 상태 딕셔너리.
        step = Step.INIT, 나머지 분석/생성 필드는 None(미계산).
    """
    from datetime import datetime

    if test_cases is None:
        test_cases = []
    if created_at is None:
        created_at = datetime.now().isoformat()
    if not group_dir and cases_path:
        p = Path(cases_path)
        group_dir = p.name if p.is_dir() else p.parent.name

    generated_file_path = (
        f"tests/generated/{group_dir}/" if group_dir else "tests/generated/test_generated.py"
    )

    return {
        "url":                url,
        "test_cases":         test_cases,
        "step":               Step.INIT,
        "created_at":         created_at,
        "cases_path":         cases_path,
        "group_dir":          group_dir,
        "dom_info":           None,
        "sub_dom_keys":       {},
        "dom_cache_key":      "",
        "plan":               None,
        "generated_file_path": generated_file_path,
        "generated_files":    [],
        "generated_code":     None,
        "lint_result":        None,
        "review_summary":     None,
        "approval_status":    None,
        "rejection_reason":   None,
        "rejection_count":    0,
        "execution_result":   None,
        "heal_count":         0,
        "heal_context":       None,
    }
