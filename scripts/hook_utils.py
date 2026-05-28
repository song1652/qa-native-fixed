"""훅 스크립트 공통 유틸리티."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from _paths import read_state

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
