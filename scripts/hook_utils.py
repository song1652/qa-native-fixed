"""훅 스크립트 공통 유틸리티."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from _paths import read_state
# _pipeline_registry는 지연 임포트(remaining_steps_hint 내부)로 순환 방지

# 상태 파일이 이 시간보다 오래되면 stale로 간주 (훅 무시)
_STALE_THRESHOLD_MINUTES = 30


def _is_stale(path: Path) -> bool:
    """상태 파일이 오래되어 이전 실행의 잔존 상태인지 판단.

    JSON 내부의 타임스탬프 필드(executed_at, created_at, analyzed_at)를 우선 사용.
    없으면 파일 mtime으로 fallback.
    """
    try:
        state = read_state(path)
        # JSON 내부 타임스탬프 (여러 필드 중 가장 최근 것)
        ts_fields = ["executed_at", "created_at", "analyzed_at"]
        latest_ts = None
        for field in ts_fields:
            val = state.get(field) or (state.get("execution_result") or {}).get(field)
            if val:
                try:
                    t = datetime.fromisoformat(val)
                    if latest_ts is None or t > latest_ts:
                        latest_ts = t
                except (ValueError, TypeError):
                    pass
        if latest_ts:
            return datetime.now() - latest_ts > timedelta(minutes=_STALE_THRESHOLD_MINUTES)
    except Exception:
        pass
    # fallback: 파일 mtime
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return datetime.now() - mtime > timedelta(minutes=_STALE_THRESHOLD_MINUTES)
    except Exception:
        return False


def check_state(path: Path, key: str, value: str, extra_check=None) -> dict | None:
    """상태 파일을 읽고 key=value 조건을 확인한다.

    Args:
        path: 상태 JSON 파일 경로
        key: 확인할 딕셔너리 키 (예: "step", "status")
        value: 기대하는 값
        extra_check: state dict를 받아 bool을 반환하는 선택적 함수.
                     False 반환 시 None을 돌려준다.

    Returns:
        조건을 모두 만족하면 state dict, 아니면 None.
        호출자는 None이면 sys.exit(0)을 수행해야 한다.
    """
    if not path.exists():
        return None

    # 이전 실행의 잔존 상태면 무시
    if _is_stale(path):
        return None

    try:
        state = read_state(path)
    except Exception:
        return None

    if state.get(key) != value:
        return None

    if extra_check is not None and not extra_check(state):
        return None

    return state


def remaining_steps_hint(from_step: str) -> list[str]:
    """from_step 이후 실행해야 할 스크립트 목록을 레지스트리 기반으로 반환 (P44).

    _pipeline_registry.PIPELINE_STEP_DEFS 정의 순서를 따르며,
    스크립트가 없는 단계(init 등)와 단말(is_terminal=True) 단계는 건너뜀.
    훅 출력의 실행 지시문을 하드코딩 대신 레지스트리에서 자동 생성해
    레지스트리 변경 시 훅 지시문도 자동 갱신된다.

    Args:
        from_step: 현재 단계 (Step.* 상수). 이 단계 이후부터 나열.

    Returns:
        "N. python <script>  # <label>" 형식의 문자열 리스트.
        from_step이 레지스트리에 없으면 빈 리스트.

    Example::

        remaining_steps_hint(Step.INIT)
        # → ["1. python scripts/01_analyze.py  # DOM 분석",
        #     "2. python scripts/02a_dialog.py  # 심의 (계획)", ...]
    """
    from _pipeline_registry import PIPELINE_STEP_DEFS
    # terminal 여부와 무관하게 모든 단계 순서 유지
    # (Step.DONE은 is_terminal=True지만 05_execute.py 실행이 필요하기 때문)
    all_steps = list(PIPELINE_STEP_DEFS)
    step_names = [s.step for s in all_steps]
    try:
        start_idx = step_names.index(from_step) + 1
    except ValueError:
        return []
    hints: list[str] = []
    for s in all_steps[start_idx:]:
        if s.script:
            hints.append(f"{len(hints) + 1}. python {s.script}  # {s.label}")
    return hints
