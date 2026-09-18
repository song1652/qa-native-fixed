"""FSM 상태 파일(state/pipeline.json 등) 원자적 read/write/update.

락 기반 원자 쓰기 + step/status 전이 검증을 담당한다. 경로 상수와 파일 락
프리미티브는 _paths 모듈 소유이므로, 여기서는 `import _paths` 후 매 호출마다
`_paths.PIPELINE_STATE` 등을 속성으로 참조한다 — 테스트가
`monkeypatch.setattr(_paths, "PIPELINE_STATE", tmp_path)` 로 경로를 치환하는
기존 방식을 그대로 지원하기 위함이다 (모듈 top-level에서 값을 복사해오면
monkeypatch가 이 모듈에 반영되지 않는다).
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import _paths


def read_state(path: Path) -> dict:
    """크로스플랫폼 락 파일 방식으로 안전하게 JSON 상태 파일을 읽는다."""
    if not path.exists():
        return {}
    lock_path = path.with_suffix(".lock")
    with _paths._file_lock(lock_path, path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            return {}


def update_state(path: Path, mutator) -> dict:
    """락 보유 중 read-modify-write를 원자적으로 수행한다.

    mutator(current: dict) -> dict 를 받아 현재 상태를 수정하고 쓴다.
    FSM 전이 검증(write_state)도 자동 적용된다.

    예시:
        update_state(PARALLEL_STATE, lambda s: {**s, "heal_count": s.get("heal_count", 0) + 1})
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")
    with _paths._file_lock(lock_path, path):
        # 락 보유 중 읽기 (read_state는 내부적으로 락을 획득하려 하므로 직접 읽기)
        current: dict = {}
        if path.exists():
            try:
                current = json.loads(path.read_text(encoding="utf-8"))
            except Exception as _parse_err:
                # 손상 JSON → 백업 후 예외 재발생 (조용한 데이터 소실 방지) (P51)
                import shutil as _shutil
                from datetime import datetime as _dt
                _ts = _dt.now().strftime("%Y%m%d_%H%M%S")
                _backup = path.with_name(f"{path.stem}.corrupt.{_ts}{path.suffix}")
                try:
                    _shutil.copy2(path, _backup)
                    print(f"[경고] {path.name} 파싱 실패 — 백업: {_backup.name}", file=sys.stderr)
                except Exception:
                    pass
                raise ValueError(f"상태 파일 파싱 실패: {path} — {_parse_err}") from _parse_err
        new_data = mutator(current)
        # 전이 검증 (락 보유 중 직접)
        if path == _paths.PIPELINE_STATE and "step" in new_data:
            _validate_transition_locked_raw(path, "step", new_data, current)
        elif path in (_paths.PARALLEL_STATE, _paths.QUICK_STATE) and "status" in new_data:
            _validate_transition_locked_raw(path, "status", new_data, current)
        content = json.dumps(new_data, ensure_ascii=False, indent=2)
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with open(fd, "w", encoding="utf-8") as f:
                f.write(content)
            Path(tmp_path).replace(path)
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise
        return new_data


def _validate_transition_locked_raw(path: Path, field: str, new_data: dict, current: dict):
    """이미 파일을 읽은 상태에서 전이 검증 (update_state 내부용)."""
    if field == "step":
        from _constants import assert_valid_transition as _check
    else:
        from _constants import assert_valid_parallel_transition as _check  # type: ignore[assignment]

    new_val = new_data.get(field, "")
    current_val = current.get(field, "")
    if not new_val or not current_val or current_val == new_val:
        return
    _check(current_val, new_val)


def reset_state(path: Path, data: dict):
    """FSM 전이 검증 없이 초기화 상태로 원자 쓰기.

    run_qa.py 재실행 시 step="init" 기록처럼 FSM 시작점을 생성할 때만 사용.
    이 함수를 쓴 후의 모든 상태 변경은 반드시 write_state() 를 통해야 한다.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")
    with _paths._file_lock(lock_path, path):
        content = json.dumps(data, ensure_ascii=False, indent=2)
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with open(fd, "w", encoding="utf-8") as f:
                f.write(content)
            Path(tmp_path).replace(path)
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise


def write_state(path: Path, data: dict):
    """원자적 쓰기 + 락으로 안전하게 JSON 상태 파일을 쓴다.

    락 파일(*.lock)을 보유한 채로 전이 검증 → 원자 쓰기를 수행하므로
    병렬 프로세스 간 RMW(Read-Modify-Write) 경쟁 조건을 방지한다.
    - pipeline.json: step 전이 규칙 검증
    - parallel.json / quick.json: status 전이 규칙 검증
    잘못된 전이 시 ValueError 발생.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")
    with _paths._file_lock(lock_path, path):
        # 락 보유 중 전이 검증 (read_state를 통하지 않고 직접 읽어 재진입 방지)
        if path == _paths.PIPELINE_STATE and "step" in data:
            _validate_transition_locked(path, "step", data)
        elif path in (_paths.PARALLEL_STATE, _paths.QUICK_STATE) and "status" in data:
            _validate_transition_locked(path, "status", data)

        content = json.dumps(data, ensure_ascii=False, indent=2)
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with open(fd, "w", encoding="utf-8") as f:
                f.write(content)
            Path(tmp_path).replace(path)
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise


def _validate_transition_locked(path: Path, field: str, new_data: dict):
    """락을 보유한 채로 step/status 전이가 유효한지 검증.

    read_state()를 호출하지 않고 직접 파일을 읽어 락 재진입(deadlock)을 방지한다.
    field: 'step' (pipeline.json) 또는 'status' (parallel.json/quick.json)
    """
    if field == "step":
        from _constants import assert_valid_transition as _check
    else:
        from _constants import assert_valid_parallel_transition as _check  # type: ignore[assignment]

    new_val = new_data.get(field, "")
    if not new_val:
        return

    # 직접 파일 읽기 (이미 락 보유 중이므로 read_state 호출 금지)
    current_val = ""
    if path.exists():
        try:
            current_val = json.loads(path.read_text(encoding="utf-8")).get(field, "")
        except Exception:
            pass

    # 초기 상태(파일 없음 or 필드 없음)에서는 검증 건너뜀
    if not current_val:
        return

    # 같은 값으로 재기록은 허용 (상태 업데이트)
    if current_val == new_val:
        return

    _check(current_val, new_val)
