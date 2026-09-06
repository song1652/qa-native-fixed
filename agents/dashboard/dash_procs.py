"""dash_procs.py — 프로세스 관리·SSE·파일 감시 (serve.py Phase-3 분리).

자식 프로세스 추적, SSE 클라이언트 관리, 파일 감시 스레드를 담당한다.
모듈 임포트 시 파일 감시 스레드를 자동으로 시작한다.
serve.py가 이 모듈을 import하고, 이 모듈은 serve를 import하지 않는다 (순환 import 방지).
"""
from __future__ import annotations

import queue
import threading
import time

from _paths import (
    DIALOG_PATH,
    PIPELINE_STATE as STATE_PATH,
    PARALLEL_STATE as PARALLEL_STATE_PATH,
    QUICK_STATE as QUICK_STATE_PATH,
    DISCUSS_STATE as DISCUSS_PATH,
)

# ── 서버가 띄운 자식 프로세스 추적 (P61) ────────────────────────
# set[int] → dict[int, Popen] 으로 변경해 liveness 확인(poll()) 가능.
# kill 전 poll()로 이미 종료된 프로세스를 확인해 PID 재사용 오살 위험 감소.
_SPAWNED_PROCS: dict = {}   # dict[int, subprocess.Popen]
_SPAWNED_PIDS_LOCK = threading.Lock()

# P77: 스크립트 태그별 실행 중 프로세스 추적 — 중복 spawn 방지.
# 대시보드 Run 버튼 더블클릭 시 동일 파이프라인이 두 번 기동되어 state 파일 충돌 발생.
# {tag: Popen} — tag는 파이프라인 종류를 나타내는 짧은 문자열.
_SCRIPT_RUNNING: dict[str, object] = {}  # dict[str, subprocess.Popen]


def _register_spawned_proc(proc, tag: str = "") -> None:
    """Popen 객체를 등록하고 죽은 프로세스를 정리한다 (P61).

    P77: tag를 지정하면 동종 프로세스를 _SCRIPT_RUNNING에도 기록해
    _is_script_running()으로 중복 실행을 사전 차단할 수 있다.
    """
    with _SPAWNED_PIDS_LOCK:
        dead = [pid for pid, p in _SPAWNED_PROCS.items() if p.poll() is not None]
        for pid in dead:
            del _SPAWNED_PROCS[pid]
        _SPAWNED_PROCS[proc.pid] = proc
        if tag:
            _SCRIPT_RUNNING[tag] = proc


def _is_script_running(tag: str) -> bool:
    """동종(같은 tag) 프로세스가 이미 실행 중인지 확인 (P77: 중복 spawn 방지)."""
    if not tag:
        return False
    with _SPAWNED_PIDS_LOCK:
        proc = _SCRIPT_RUNNING.get(tag)
        return proc is not None and proc.poll() is None  # type: ignore[union-attr]


# 하위 호환 별칭 — 기존 호출부(proc.pid 전달)가 있을 경우를 위해 유지.
def _register_spawned_pid(pid: int):  # type: ignore[override]
    pass  # 직접 PID만 전달하는 구 호출 경로. _register_spawned_proc를 쓸 것.


def _is_spawned_pid(pid: int) -> bool:
    with _SPAWNED_PIDS_LOCK:
        return pid in _SPAWNED_PROCS


# ── SSE 클라이언트 관리 ────────────────────────────────────────
_sse_clients: list[queue.Queue] = []
_sse_lock = threading.Lock()


def _sse_notify():
    """파일 변경 시 모든 SSE 클라이언트에 알림."""
    with _sse_lock:
        dead = []
        for q in _sse_clients:
            try:
                q.put_nowait("update")
            except queue.Full:
                dead.append(q)
        for q in dead:
            _sse_clients.remove(q)


def _watch_files():
    """dialog.json / state/*.json mtime을 0.3초마다 감시."""
    watched = [DIALOG_PATH, DISCUSS_PATH, STATE_PATH, PARALLEL_STATE_PATH,
               QUICK_STATE_PATH]
    last_mtimes = {p: 0.0 for p in watched}
    while True:
        for p in watched:
            try:
                mtime = p.stat().st_mtime if p.exists() else 0.0
                if mtime != last_mtimes[p]:
                    last_mtimes[p] = mtime
                    _sse_notify()
            except Exception:
                pass
        time.sleep(0.3)


# 파일 감시 스레드 시작 (모듈 임포트 시 자동 기동)
threading.Thread(target=_watch_files, daemon=True).start()
