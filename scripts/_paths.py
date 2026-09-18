from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

# 파일 락 기본 대기 시간(초)
LOCK_TIMEOUT_SECS = 10.0
# 스테일 임계값은 타임아웃보다 충분히 커야 한다.
# 두 값이 같으면 락을 정상적으로 오래 들고 있는 프로세스의 락을
# 대기 중인 다른 프로세스가 조기에 강탈해 상호 배제가 깨진다.
LOCK_STALE_SECS = 60.0


def _acquire_file_lock(
    lock_path: Path,
    timeout_secs: float = LOCK_TIMEOUT_SECS,
    stale_secs: float | None = None,
) -> bool:
    """크로스플랫폼 락 파일 획득 (스핀락). 획득 성공 시 True.

    stale_secs를 지정하지 않으면 max(timeout_secs * 3, LOCK_STALE_SECS)를 사용한다.
    스테일 임계값이 타임아웃보다 크므로, 대기 중인 프로세스가 아직 살아 있는
    보유자의 락을 강탈하지 않는다.
    """
    if stale_secs is None:
        stale_secs = max(timeout_secs * 3, LOCK_STALE_SECS)
    deadline = time.monotonic() + timeout_secs
    while time.monotonic() < deadline:
        try:
            lock_path.touch(exist_ok=False)  # 원자적 생성 — 이미 존재하면 FileExistsError
            return True
        except FileExistsError:
            # stale_secs 이상 방치된 스테일 락(비정상 종료 잔재)만 강제 제거
            try:
                if lock_path.exists() and (time.time() - lock_path.stat().st_mtime) > stale_secs:
                    lock_path.unlink(missing_ok=True)
            except OSError:
                pass
            time.sleep(0.05)
    return False


def _release_file_lock(lock_path: Path):
    """락 파일 해제."""
    lock_path.unlink(missing_ok=True)


@contextmanager
def _file_lock(lock_path: Path, target: Path, timeout_secs: float = LOCK_TIMEOUT_SECS):
    """락 획득을 강제하는 컨텍스트 매니저. 실패 시 TimeoutError.

    락 획득 실패를 무시하고 진행하면 상호 배제가 없는 상태로 파일을
    읽고 쓰게 되므로, 실패는 조용히 넘기지 않고 예외로 승격한다.
    """
    if not _acquire_file_lock(lock_path, timeout_secs):
        raise TimeoutError(
            f"파일 락 획득 실패 ({timeout_secs}초 초과): {target} (lock={lock_path})"
        )
    try:
        yield
    finally:
        _release_file_lock(lock_path)

# Windows cp949 터미널에서 한글/유니코드 출력 깨짐 방지
# pytest 실행 시에는 캡처 스트림을 재래핑하지 않음 (I/O closed 충돌 방지)
_under_pytest = "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ
if not _under_pytest and sys.stdout and hasattr(sys.stdout, "buffer"):
    try:
        # M-1(P133): 재래핑 전 버퍼 플러시 — 미플러시 데이터가 new TextIOWrapper에 유실되는 것을 방지
        sys.stdout.flush()
        sys.stderr.flush()
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

# 테스트 아티팩트
GENERATED_DIR = PROJECT_ROOT / "tests" / "generated"
REPORTS_DIR = PROJECT_ROOT / "tests" / "reports"
SCREENSHOTS_DIR = PROJECT_ROOT / "tests" / "screenshots"
VIDEOS_DIR = PROJECT_ROOT / "tests" / "videos"
IMPORT_DIR = PROJECT_ROOT / "import"

# 힐링·통계
HEAL_STATS_PATH = STATE_DIR / "heal_stats.json"
FLAKY_TESTS_PATH = STATE_DIR / "flaky_tests.json"

# Import Studio 상태 파일 (S2 BE)
IMPORT_SESSIONS_DIR  = STATE_DIR / "import_sessions"
IMPORT_SNAPSHOTS_DIR = STATE_DIR / "import_snapshots"
IMPORT_PROFILES_PATH = STATE_DIR / "import_profiles.json"

PAGES_JSON    = PROJECT_ROOT / "config" / "pages.json"
TESTCASES_DIR = PROJECT_ROOT / "testcases"

# 팀 토론·구현 대기 파일 (Phase-2: serve.py → _paths 단일 소스)
DIALOG_PATH      = PROJECT_ROOT / "agents" / "dialog.json"
TEAM_NOTES_PATH  = PROJECT_ROOT / "agents" / "team_notes.md"
PENDING_IMPL_PATH = PROJECT_ROOT / "pending_impl.json"

# 프로덕트별 테스트 데이터 (test_data/{product}.json)
TEST_DATA_DIR  = PROJECT_ROOT / "test_data"


def load_test_data() -> dict:
    """test_data/ 폴더의 프로덕트별 JSON을 머지해 반환.

    파일명(stem)이 곧 data_key(product key)가 된다.
      test_data/serveone.json  → result["serveone"]
      test_data/saucedemo.json → result["saucedemo"]

    *.example.json, _로 시작하는 파일, _comment 키는 제외한다.
    파일이 없으면 빈 dict 반환 (시스템 정지 없음).
    """
    result: dict = {}
    if not TEST_DATA_DIR.exists():
        return result
    for fpath in sorted(TEST_DATA_DIR.glob("*.json")):
        if fpath.name.endswith(".example.json") or fpath.stem.startswith("_"):
            continue
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            data.pop("_comment", None)
            result[fpath.stem] = data
        except (json.JSONDecodeError, OSError):
            pass
    return result


def is_spa_group(group: "list[str] | None") -> bool:
    """그룹 목록 중 하나라도 pages.json에서 spa:true 설정을 가지면 True.

    L-5(P127): 단일 소스 — scripts/05_execute.py와 parallel/_exec.py가 공유.
    두 파일에서 복붙하던 코드를 이 함수 한 곳으로 통합한다.

    group=None (전체 실행)이면 pages.json 전 항목을 검사한다 (_exec.py 동일 동작 유지).
    """
    if not PAGES_JSON.exists():
        return False
    try:
        pages_cfg: dict = json.loads(PAGES_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as _e:  # M-6(P138): 파싱 실패 시 non-SPA로 처리
        print(f"[_paths] is_spa_group: pages.json 파싱 실패 ({_e}) → non-SPA 처리")
        return False
    check_keys = group if group else [k for k in pages_cfg if not k.startswith("_")]
    for g in check_keys:
        cfg = pages_cfg.get(g, {})
        if isinstance(cfg, dict) and cfg.get("spa", False):
            return True
    return False


def append_run_history(entry: dict):
    """실행 이력을 state/run_history.json에 append한다.

    read-modify-write 전체를 락 파일로 보호해 병렬 파이프라인에서의
    동시 쓰기로 인한 데이터 유실을 방지한다 (Windows 포함 크로스플랫폼).
    """
    RUN_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    lock_path = RUN_HISTORY.with_suffix(".lock")
    with _file_lock(lock_path, RUN_HISTORY):
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


# FSM 상태 read/write/update 로직은 _state.py로 분리했다.
# 경로 상수와 파일 락은 이 모듈이 계속 소유하며, _state.py가 매 호출마다
# `_paths.PIPELINE_STATE` 등을 속성으로 참조하므로 monkeypatch(_paths, ...) 기반
# 기존 테스트는 그대로 동작한다. 아래는 하위 호환을 위한 재노출(re-export).
from _state import (  # noqa: E402,F401 — 하위 호환 재노출
    read_state,
    write_state,
    update_state,
    reset_state,
    _validate_transition_locked,
    _validate_transition_locked_raw,
)

# 하위 호환 alias (외부에서 직접 import하는 코드 대비)
_validate_step_transition_locked = _validate_transition_locked
