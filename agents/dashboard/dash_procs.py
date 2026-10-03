"""dash_procs.py — 프로세스 관리·SSE·파일 감시 (serve.py Phase-3 분리).

자식 프로세스 추적, SSE 클라이언트 관리, 파일 감시 스레드를 담당한다.
모듈 임포트 시 파일 감시 스레드를 자동으로 시작한다.
serve.py가 이 모듈을 import하고, 이 모듈은 serve를 import하지 않는다 (순환 import 방지).
"""
from __future__ import annotations

import queue
import threading
import time

import _paths

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
    watched = [_paths.DIALOG_PATH, _paths.DISCUSS_STATE, _paths.PIPELINE_STATE, _paths.PARALLEL_STATE,
               _paths.QUICK_STATE, _paths.RUN_HISTORY]
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


EXECUTION_TIMEOUT_SECONDS = 3600


def _execution_path():
    return _paths.STATE_DIR / 'dashboard_execution.json'


def _process_identity(pid):
    """Check process birth and session ownership before signalling a recovered PID."""
    import os
    import subprocess
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.windll.kernel32
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        kernel.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(ctypes.c_ulonglong)] * 4
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        process = kernel.OpenProcess(0x1000, False, int(pid))
        if not process:
            return ''
        try:
            exit_code = ctypes.c_ulong()
            if not kernel.GetExitCodeProcess(process, ctypes.byref(exit_code)) or exit_code.value != 259:
                return ''
            times = [ctypes.c_ulonglong() for _ in range(4)]
            if kernel.GetProcessTimes(process, *(ctypes.byref(value) for value in times)):
                return str(times[0].value)
            return ''
        finally:
            kernel.CloseHandle(process)
    try:
        return subprocess.check_output(
            ['ps', '-p', str(pid), '-o', 'lstart=', '-o', 'pgid='],
            text=True, timeout=2,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return ''


def _owned_process_alive(run):
    pid = run.get('pid')
    if not pid:
        return False
    with _SPAWNED_PIDS_LOCK:
        proc = _SPAWNED_PROCS.get(pid)
    if proc is not None:
        return proc.poll() is None
    identity = _process_identity(pid)
    return bool(identity and identity == run.get('process_identity'))


PROCESS_STOP_GRACE_SECONDS = 3


def _process_group_alive(run):
    import os
    if os.name == 'nt':
        return _owned_process_alive(run)
    # Reap our launcher while checking the group's surviving children.
    _owned_process_alive(run)
    identity = _process_identity(run['pid'])
    if identity and identity != run.get('process_identity'):
        return False  # A reused PID cannot own the old process group.
    try:
        os.killpg(run['pid'], 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # macOS can report EPERM while an orphaned group is being reaped.
        return True


def _stop_process_group(run):
    import os
    import signal
    import subprocess
    if not _owned_process_alive(run) and not run.get('stopping') and not (
        run.get('process_identity') and _process_group_alive(run)
    ):
        return
    pid = run['pid']
    if os.name == 'nt':
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)],
                       capture_output=True, timeout=5, check=True)
    else:
        if not run.get('stopping'):
            os.killpg(pid, signal.SIGTERM)
        deadline = time.monotonic() + PROCESS_STOP_GRACE_SECONDS
        while _process_group_alive(run) and time.monotonic() < deadline:
            time.sleep(.02)
        if _process_group_alive(run):
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + PROCESS_STOP_GRACE_SECONDS
        while _process_group_alive(run) and time.monotonic() < deadline:
            time.sleep(.02)
        if _process_group_alive(run):
            raise TimeoutError('Execution process group is still stopping')
    with _SPAWNED_PIDS_LOCK:
        proc = _SPAWNED_PROCS.get(pid)
    if proc is not None:
        proc.wait(timeout=3)


def _finish_execution(run, status, error=''):
    from datetime import datetime
    from error_policy import recovery_for_result
    from run_results import read_execution_result, write_execution_result
    run_id = run['run_id']
    owned = read_execution_result(_paths.PROJECT_ROOT, run_id) or {}
    if not owned and status == 'failed':
        logs = _paths.LOGS_DIR / 'runs'
        for name in (f'{run_id}.txt', f'{run_id}-headless.txt'):
            try:
                with (logs / name).open('rb') as stream:
                    stream.seek(0, 2)
                    stream.seek(max(0, stream.tell() - 4096))
                    error += '\n' + stream.read().decode('utf-8', errors='replace')
            except OSError:
                pass
    # Normal completion uses owned outcomes; process exit alone never means PASS.
    if status is None:
        status = owned.get('status')
        if status not in {'passed', 'failed', 'cancelled', 'timed_out', 'interrupted', 'incomplete'}:
            status = 'interrupted'
            error = 'Dashboard execution stopped before a terminal result was saved.'
    finished_at = datetime.now().isoformat()
    if status in {'cancelled', 'timed_out', 'interrupted'} or not owned or (status == 'failed' and owned.get('status') != 'failed'):
        owned = {**owned, 'run_id': run_id, 'workflow_id': run_id, 'status': status,
                 'started_at': run['started_at'], 'finished_at': finished_at,
                 'groups': run.get('groups', []), 'error': error, 'report_path': owned.get('report_path')}
        owned['recovery'] = recovery_for_result(owned)
        owned = write_execution_result(_paths.PROJECT_ROOT, run_id, owned)
        status = owned['status']
        _paths.append_run_history({**owned, 'timestamp': finished_at,
                                   'pipeline': run.get('pipeline', 'single')})
    target = {'run_qa': _paths.PIPELINE_STATE, 'run_qa_parallel': _paths.PARALLEL_STATE,
              'run_merge': _paths.PARALLEL_STATE, 'run_quick': _paths.QUICK_STATE}[run['tag']]
    _paths.update_state(target, lambda fresh: {
        **fresh, 'workflow_status': status, 'execution_result': owned,
    } if fresh.get('run_id') == run_id else fresh)
    return {**run, 'status': status, 'finished_at': finished_at, 'error': error}


def _reconcile_execution(run):
    if run.get('status') != 'running':
        return run
    if run.get('stopping'):
        try:
            _stop_process_group(run)
        except (OSError, TimeoutError):
            return run
        return _finish_execution(run, run.get('stop_status', 'cancelled'), 'Execution stopped by supervisor.')
    if _owned_process_alive(run) or (run.get('process_identity') and _process_group_alive(run)):
        if time.time() - run.get('started_epoch', time.time()) <= EXECUTION_TIMEOUT_SECONDS:
            return run
        try:
            _stop_process_group(run)
        except (OSError, TimeoutError):
            return {**run, 'stopping': True, 'stop_status': 'timed_out'}
        return _finish_execution(run, 'timed_out', 'Dashboard execution exceeded its time limit.')
    with _SPAWNED_PIDS_LOCK:
        proc = _SPAWNED_PROCS.get(run.get('pid'))
    exit_code = proc.poll() if proc is not None else None
    if exit_code is not None and exit_code != 0:
        return _finish_execution(run, 'failed', f'Dashboard launcher exited with code {exit_code}.')
    return _finish_execution(run, None)


def execution_status():
    """Recover a live launch after restart, or preserve its owned terminal outcome."""
    return _paths.update_state(_execution_path(), _reconcile_execution)


def start_execution(command, tag, *, groups=None, legacy_log=None, prepare=None):
    """Reserve all dashboard QA execution types under one durable file lock."""
    import os
    import subprocess
    import uuid
    from datetime import datetime
    response = {}

    def launch(current):
        current = _reconcile_execution(current)
        if current.get('status') == 'running':
            response.update(ok=False, error='QA execution already running', run_id=current['run_id'])
            return current
        if prepare:
            prepare()
        run_id = uuid.uuid4().hex
        logs = _paths.LOGS_DIR / 'runs'
        logs.mkdir(parents=True, exist_ok=True)
        log_path = logs / f'{run_id}.txt'
        target = {'run_qa': _paths.PIPELINE_STATE, 'run_qa_parallel': _paths.PARALLEL_STATE,
                  'run_merge': _paths.PARALLEL_STATE, 'run_quick': _paths.QUICK_STATE}[tag]
        _paths.update_state(target, lambda state: {
            **{key: value for key, value in state.items()
               if key not in {'execution_result', 'error', 'heal_subagent_contexts'}},
            'run_id': run_id, 'last_run_id': run_id, 'workflow_status': 'running',
        })
        run = {'run_id': run_id, 'tag': tag, 'status': 'running',
               'pipeline': 'quick' if tag == 'run_quick' else ('single' if tag == 'run_qa' else 'parallel'),
               'groups': groups or [], 'started_at': datetime.now().isoformat(),
               'started_epoch': time.time(), 'log_name': log_path.name}
        try:
            env = {**os.environ, 'QA_RUN_ID': run_id, 'QA_WORKFLOW_ID': run_id}
            with log_path.open('w', encoding='utf-8') as log_file:
                proc = subprocess.Popen(command, cwd=str(_paths.PROJECT_ROOT), env=env,
                                        stdout=log_file, stderr=subprocess.STDOUT,
                                        start_new_session=os.name != 'nt')
            _register_spawned_proc(proc, tag)
            run.update(pid=proc.pid, process_identity=_process_identity(proc.pid))
            if legacy_log:
                alias = _paths.LOGS_DIR / legacy_log
                alias.unlink(missing_ok=True)
                try:
                    alias.symlink_to(log_path)
                except OSError:
                    # Windows may disallow symlinks; new clients use the owned log.
                    pass
            response.update(ok=True, pid=proc.pid, run_id=run_id,
                            log=str(log_path), log_name=log_path.name, status='running')
            return run
        except (OSError, subprocess.SubprocessError) as error:
            failed = _finish_execution(run, 'failed', str(error))
            response.update(ok=False, error=str(error), run_id=run_id)
            return failed

    _paths.update_state(_execution_path(), launch)
    return response


def cancel_execution(run_id):
    import subprocess
    response = {}

    def cancel(current):
        current = _reconcile_execution(current)
        if not run_id or current.get('run_id') != run_id:
            response.update(ok=False, error='Execution does not belong to this run')
            return current
        if current.get('status') != 'running':
            response.update(ok=True, run_id=run_id, status=current.get('status'))
            return current
        try:
            _stop_process_group(current)
        except (OSError, TimeoutError, subprocess.SubprocessError) as error:
            response.update(ok=False, error=str(error), run_id=run_id)
            return {**current, 'stopping': True, 'stop_status': 'cancelled'}
        completed = _finish_execution(current, 'cancelled', 'Execution cancelled by user.')
        response.update(ok=True, run_id=run_id, status='cancelled')
        return completed

    _paths.update_state(_execution_path(), cancel)
    return response


def _watch_execution():
    while True:
        try:
            if _execution_path().exists():
                execution_status()
        except Exception as error:
            print(f'[Dashboard] execution reconciliation failed: {error}')
        time.sleep(1)


threading.Thread(target=_watch_execution, daemon=True).start()


def run_when_idle(operation):
    """Keep reset writes under the same admission lock used for launching."""
    applied = False

    def apply(current):
        nonlocal applied
        current = _reconcile_execution(current)
        if current.get('status') != 'running':
            operation()
            applied = True
        return current

    _paths.update_state(_execution_path(), apply)
    return applied
