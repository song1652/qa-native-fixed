from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path


def _acquire_file_lock(lock_path: Path, timeout_secs: float = 10.0) -> bool:
    """크로스플랫폼 락 파일 획득 (스핀락). 획득 성공 시 True."""
    deadline = time.monotonic() + timeout_secs
    while time.monotonic() < deadline:
        try:
            lock_path.touch(exist_ok=False)  # 원자적 생성 — 이미 존재하면 FileExistsError
            return True
        except FileExistsError:
            # 10초 이상 방치된 스테일 락은 강제 제거
            try:
                if lock_path.exists() and (time.time() - lock_path.stat().st_mtime) > 10:
                    lock_path.unlink(missing_ok=True)
            except OSError:
                pass
            time.sleep(0.05)
    return False


def _release_file_lock(lock_path: Path):
    """락 파일 해제."""
    lock_path.unlink(missing_ok=True)

# Windows cp949 터미널에서 한글/유니코드 출력 깨짐 방지
# pytest 실행 시에는 캡처 스트림을 재래핑하지 않음 (I/O closed 충돌 방지)
_under_pytest = "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ
if not _under_pytest and sys.stdout and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 상태 파일
STATE_DIR = PROJECT_ROOT / "state"
PIPELINE_STATE = STATE_DIR / "pipeline.json"
DISCUSS_STATE = STATE_DIR / "discuss.json"
PARALLEL_STATE = STATE_DIR / "parallel.json"
QUICK_STATE = STATE_DIR / "quick.json"
HEAL_CONTEXT_STATE = STATE_DIR / "heal_context.json"
RUN_HISTORY = STATE_DIR / "run_history.json"

# DOM 캐시
DOM_CACHE_DIR = STATE_DIR / "dom_cache"
DOM_CACHE_TTL_HOURS = int(os.environ.get("DOM_CACHE_TTL_HOURS", "168"))          # 정적 DOM: 7일
DOM_DYNAMIC_CACHE_TTL_HOURS = int(os.environ.get("DOM_DYNAMIC_CACHE_TTL_HOURS", "24"))  # 동적 DOM: 24시간

# 로그 파일
LOGS_DIR = PROJECT_ROOT / "logs"
RUN_QA_LOG = LOGS_DIR / "run_qa.txt"
RUN_PARALLEL_LOG = LOGS_DIR / "run_parallel.txt"
MERGE_LOG = LOGS_DIR / "merge.txt"
QUICK_RUN_LOG = LOGS_DIR / "quick_run.txt"


def append_run_history(entry: dict):
    """실행 이력을 state/run_history.json에 append한다.

    read-modify-write 전체를 락 파일로 보호해 병렬 파이프라인에서의
    동시 쓰기로 인한 데이터 유실을 방지한다 (Windows 포함 크로스플랫폼).
    """
    RUN_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    lock_path = RUN_HISTORY.with_suffix(".lock")
    acquired = _acquire_file_lock(lock_path)
    try:
        history = []
        if RUN_HISTORY.exists():
            try:
                history = json.loads(RUN_HISTORY.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, Exception):
                history = []
        history.append(entry)
        content = json.dumps(history, ensure_ascii=False, indent=2)
        fd, tmp_path = tempfile.mkstemp(dir=RUN_HISTORY.parent, suffix=".tmp")
        try:
            with open(fd, "w", encoding="utf-8") as f:
                f.write(content)
            Path(tmp_path).replace(RUN_HISTORY)
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise
    finally:
        if acquired:
            _release_file_lock(lock_path)


def url_cache_key(url: str) -> str:
    """URL을 MD5 해시해 캐시 파일명으로 사용."""
    return hashlib.md5(url.encode()).hexdigest()


def get_cached_dom(url: str) -> dict | None:
    """캐시된 DOM 분석 결과가 있으면 반환.

    - 정적 DOM: _cached_at 기준 DOM_CACHE_TTL_HOURS(7일) 초과 시 None
    - 동적 요소: _dynamic_cached_at 기준 DOM_DYNAMIC_CACHE_TTL_HOURS(24시간) 초과 시
                dynamic_elements / contextmenu_elements 필드만 제거 후 반환
    """
    cache_file = DOM_CACHE_DIR / f"{hashlib.md5(url.encode()).hexdigest()}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))

            # 정적 DOM TTL 체크
            cached_at = data.get("_cached_at")
            if DOM_CACHE_TTL_HOURS > 0:
                if not cached_at:
                    # 레거시 캐시(_cached_at 없음): mtime 기반 fallback
                    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if datetime.now() - mtime > timedelta(hours=DOM_CACHE_TTL_HOURS):
                        return None
                else:
                    try:
                        ts = datetime.fromisoformat(cached_at)
                        if datetime.now() - ts > timedelta(hours=DOM_CACHE_TTL_HOURS):
                            return None  # 정적 DOM 만료 → 전체 재분석
                    except (ValueError, TypeError):
                        pass

            # 동적 요소 TTL 체크 — 만료 시 동적 필드만 제거
            dynamic_cached_at = data.get("_dynamic_cached_at")
            if dynamic_cached_at and DOM_DYNAMIC_CACHE_TTL_HOURS > 0:
                try:
                    ts = datetime.fromisoformat(dynamic_cached_at)
                    if datetime.now() - ts > timedelta(hours=DOM_DYNAMIC_CACHE_TTL_HOURS):
                        data = {k: v for k, v in data.items()
                                if k not in ("dynamic_elements", "contextmenu_elements",
                                             "_dynamic_cached_at")}
                except (ValueError, TypeError):
                    pass

            return data
        except Exception:
            pass
    return None


def save_dom_cache(url: str, dom: dict):
    """DOM 분석 결과를 캐시에 저장.

    동적 요소(dynamic_elements, contextmenu_elements)가 있으면
    _dynamic_cached_at 타임스탬프를 별도로 기록해 TTL을 독립 관리한다.
    """
    DOM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat()
    cache_data = {**dom, "_cached_at": now}
    if "dynamic_elements" in dom or "contextmenu_elements" in dom:
        cache_data["_dynamic_cached_at"] = now
    cache_file = DOM_CACHE_DIR / f"{hashlib.md5(url.encode()).hexdigest()}.json"
    content = json.dumps(cache_data, ensure_ascii=False, indent=2)
    fd, tmp_path = tempfile.mkstemp(dir=DOM_CACHE_DIR, suffix=".tmp")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(content)
        Path(tmp_path).replace(cache_file)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def resolve_sub_doms(state: dict) -> dict:
    """sub_dom_keys에서 캐시 파일을 로드하여 {url: dom} 매핑 반환."""
    sub_dom_keys = state.get("sub_dom_keys", {})
    result = {}
    for url in sub_dom_keys:
        dom = get_cached_dom(url)
        if dom:
            result[url] = dom
    return result


def read_state(path: Path) -> dict:
    """크로스플랫폼 락 파일 방식으로 안전하게 JSON 상태 파일을 읽는다."""
    if not path.exists():
        return {}
    lock_path = path.with_suffix(".lock")
    acquired = _acquire_file_lock(lock_path)
    try:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            return {}
    finally:
        if acquired:
            _release_file_lock(lock_path)


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
    acquired = _acquire_file_lock(lock_path)
    try:
        # 락 보유 중 전이 검증 (read_state를 통하지 않고 직접 읽어 재진입 방지)
        if path == PIPELINE_STATE and "step" in data:
            _validate_transition_locked(path, "step", data)
        elif path in (PARALLEL_STATE, QUICK_STATE) and "status" in data:
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
    finally:
        if acquired:
            _release_file_lock(lock_path)


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


# 하위 호환 alias (외부에서 직접 import하는 코드 대비)
_validate_step_transition_locked = _validate_transition_locked
