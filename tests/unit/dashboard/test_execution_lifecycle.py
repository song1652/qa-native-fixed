"""Dashboard execution ownership and process cleanup use real subprocesses."""
import concurrent.futures
import json
import os
from pathlib import Path
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[3]
for folder in (ROOT / 'scripts', ROOT / 'agents' / 'dashboard'):
    sys.path.insert(0, str(folder))
import _paths
import dash_procs


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    for name, path in {'PROJECT_ROOT': tmp_path, 'STATE_DIR': tmp_path / 'state',
                       'LOGS_DIR': tmp_path / 'logs', 'RUN_HISTORY': tmp_path / 'state/run_history.json',
                       'PIPELINE_STATE': tmp_path / 'state/pipeline.json',
                       'PARALLEL_STATE': tmp_path / 'state/parallel.json',
                       'QUICK_STATE': tmp_path / 'state/quick.json'}.items():
        monkeypatch.setattr(_paths, name, path)
    yield tmp_path
    if hasattr(dash_procs, 'execution_status'):
        current = dash_procs.execution_status()
        if current.get('status') == 'running':
            dash_procs.cancel_execution(current['run_id'])
    dash_procs._SPAWNED_PROCS.clear()
    dash_procs._SCRIPT_RUNNING.clear()


def test_atomic_admission_rejects_concurrent_pipeline_types(isolated):
    command = [sys.executable, '-c', 'import time; time.sleep(30)']
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda tag: dash_procs.start_execution(command, tag),
                                ['run_qa', 'run_quick']))
    assert sum(result['ok'] for result in results) == 1
    winner = next(result for result in results if result['ok'])
    assert winner['run_id'] and winner['log_name']
    assert dash_procs.execution_status()['run_id'] == winner['run_id']


def test_cancel_stops_process_group_and_keeps_owned_terminal_result(isolated):
    marker = isolated / 'child.pid'
    code = ('import subprocess,time,pathlib,sys; '
            'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); '
            f'pathlib.Path({str(marker)!r}).write_text(str(p.pid)); time.sleep(30)')
    result = dash_procs.start_execution([sys.executable, '-c', code], 'run_quick')
    deadline = time.monotonic() + 3
    while not marker.exists() and time.monotonic() < deadline:
        time.sleep(.02)
    assert marker.exists()
    child = int(marker.read_text())
    cancelled = dash_procs.cancel_execution(result['run_id'])
    assert cancelled['ok'], cancelled
    assert dash_procs.execution_status()['status'] == 'cancelled'
    assert dash_procs.cancel_execution('foreign_run')['ok'] is False
    from run_results import read_execution_result
    owned = read_execution_result(isolated, result['run_id'])
    assert owned['status'] == 'cancelled'
    assert owned['run_id'] == result['run_id']
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            os.kill(child, 0)
        except ProcessLookupError:
            break
        time.sleep(.02)
    else:
        pytest.fail('cancel left the child running')


def test_restart_blocks_live_owned_process_and_reconciles_its_exit(isolated):
    result = dash_procs.start_execution([sys.executable, '-c', 'import time; time.sleep(.3)'], 'run_quick')
    proc = dash_procs._SPAWNED_PROCS[result['pid']]
    dash_procs._SPAWNED_PROCS.clear()
    dash_procs._SCRIPT_RUNNING.clear()
    assert dash_procs.execution_status()['status'] == 'running'
    blocked = dash_procs.start_execution([sys.executable, '-c', 'pass'], 'run_qa')
    assert blocked['ok'] is False
    proc.wait(timeout=3)
    recovered = dash_procs.execution_status()
    assert recovered['run_id'] == result['run_id']
    assert recovered['status'] == 'interrupted'
    history = json.loads(_paths.RUN_HISTORY.read_text())
    assert history[-1]['run_id'] == result['run_id']
    assert history[-1]['report_path'] is None


def test_spawn_failure_releases_admission_with_owned_failure(isolated):
    failed = dash_procs.start_execution(['/missing/qa/executable'], 'run_qa')
    assert failed['ok'] is False
    assert dash_procs.execution_status()['status'] == 'failed'
    subsequent = dash_procs.start_execution([sys.executable, '-c', 'import time; time.sleep(30)'], 'run_quick')
    assert subsequent['ok'] is True


def test_supervisor_times_out_the_owned_process(isolated, monkeypatch):
    monkeypatch.setattr(dash_procs, 'EXECUTION_TIMEOUT_SECONDS', .05)
    launched = dash_procs.start_execution([sys.executable, '-c', 'import time; time.sleep(30)'], 'run_quick')
    time.sleep(.1)
    assert dash_procs.execution_status()['status'] == 'timed_out'
    from run_results import read_execution_result
    assert read_execution_result(isolated, launched['run_id'])['status'] == 'timed_out'


def test_http_status_cancel_and_log_are_run_owned(isolated):
    from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
    launched = dash_procs.start_execution(
        [sys.executable, '-u', '-c', 'import time; print("owned-log"); time.sleep(30)'], 'run_quick')
    with dashboard_server(isolated) as base_url:
        status, response = request_json(base_url, 'GET', '/api/execution_status')
        assert status == 200
        assert response['execution']['run_id'] == launched['run_id']
        time.sleep(.05)
        _, log = request_json(base_url, 'POST', '/api/run_log', {'run_id': launched['run_id']})
        assert 'owned-log' in log['log']
        _, foreign = request_json(base_url, 'POST', '/api/run_log', {'run_id': '../escape'})
        assert foreign['ok'] is False
        _, blocked = request_json(base_url, 'POST', '/api/reset/all', {})
        assert blocked['ok'] is False
        _, cancelled = request_json(base_url, 'POST', '/api/cancel', {'run_id': launched['run_id']})
        assert cancelled['ok'] is True
        assert cancelled['status'] == 'cancelled'


def test_reset_and_launch_share_the_admission_lock(isolated):
    import threading
    entered, release = threading.Event(), threading.Event()

    def reset_action():
        entered.set()
        assert release.wait(timeout=2)

    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        reset = pool.submit(dash_procs.run_when_idle, reset_action)
        assert entered.wait(timeout=2)
        launch = pool.submit(dash_procs.start_execution,
                             [sys.executable, '-c', 'import time; time.sleep(30)'], 'run_quick')
        time.sleep(.05)
        assert not launch.done()
        release.set()
        assert reset.result(timeout=2) is True
        assert launch.result(timeout=2)['ok'] is True


def test_nonzero_launcher_does_not_publish_interim_test_pass_as_workflow_success(isolated):
    code = ('import json,os,pathlib,sys; rid=os.environ["QA_RUN_ID"]; '
            'p=pathlib.Path("state/runs")/rid/"execution_result.json"; '
            'p.parent.mkdir(parents=True,exist_ok=True); '
            'p.write_text(json.dumps({"run_id":rid,"status":"passed","passed":1,"failed":0})); '
            'sys.exit(2)')
    launched = dash_procs.start_execution([sys.executable, '-c', code], 'run_qa')
    dash_procs._SPAWNED_PROCS[launched['pid']].wait(timeout=3)
    completed = dash_procs.execution_status()
    assert completed['status'] == 'failed'
    from run_results import read_execution_result
    owned = read_execution_result(isolated, launched['run_id'])
    assert owned['status'] == 'failed'
    assert owned['passed'] == 1
    assert owned['failed'] == 0
    assert 'exit' in owned['error'].lower()


def test_startup_failure_uses_only_the_owned_log_for_recovery(isolated):
    code = 'import sys; print("browserType.launch: Executable doesn\'t exist; playwright install"); sys.exit(1)'
    launched = dash_procs.start_execution([sys.executable, '-c', code], 'run_qa')
    dash_procs._SPAWNED_PROCS[launched['pid']].wait(timeout=3)
    assert dash_procs.execution_status()['status'] == 'failed'
    from run_results import read_execution_result
    owned = read_execution_result(isolated, launched['run_id'])
    assert owned['recovery']['category'] == 'browser_unavailable'
    assert owned['report_path'] is None


def test_cancel_allows_child_rollback_after_launcher_exits(isolated):
    ready, rollback = isolated / 'child.ready', isolated / 'rollback.done'
    child_code = ('import signal,time,pathlib,sys\n'
                  'def rollback(signum, frame):\n'
                  ' time.sleep(.4)\n'
                  f' pathlib.Path({str(rollback)!r}).write_text("restored")\n'
                  ' sys.exit(0)\n'
                  'signal.signal(signal.SIGTERM, rollback)\n'
                  f'pathlib.Path({str(ready)!r}).write_text("ready")\n'
                  'time.sleep(30)\n')
    parent_code = ('import subprocess,sys,time; '
                   f'subprocess.Popen([sys.executable,"-c",{child_code!r}]); time.sleep(30)')
    launched = dash_procs.start_execution([sys.executable, '-c', parent_code], 'run_quick')
    deadline = time.monotonic() + 3
    while not ready.exists() and time.monotonic() < deadline:
        time.sleep(.02)
    assert ready.exists()
    assert dash_procs.cancel_execution(launched['run_id'])['ok'] is True
    assert rollback.read_text() == 'restored'
    assert dash_procs.execution_status()['status'] == 'cancelled'


def test_terminal_summary_updates_only_its_matching_latest_state(isolated):
    launched = dash_procs.start_execution([sys.executable, '-c', 'import time; time.sleep(30)'], 'run_quick')
    _paths.update_state(_paths.QUICK_STATE, lambda state: {**state, 'status': 'testing'})
    assert dash_procs.cancel_execution(launched['run_id'])['ok'] is True
    latest = json.loads(_paths.QUICK_STATE.read_text())
    assert latest['status'] == 'testing'
    assert latest['workflow_status'] == 'cancelled'
    assert latest['execution_result']['status'] == 'cancelled'
    assert latest['execution_result']['run_id'] == launched['run_id']
    restarted = dash_procs.start_execution([sys.executable, '-c', 'import time; time.sleep(30)'], 'run_quick')
    assert json.loads(_paths.QUICK_STATE.read_text()).get('workflow_status') == 'running'
    _paths.update_state(_paths.QUICK_STATE, lambda state: {**state, 'run_id': 'newer_owner',
                                                        'execution_result': {'run_id': 'newer_owner', 'passed': 7}})
    assert dash_procs.cancel_execution(restarted['run_id'])['ok'] is True
    latest = json.loads(_paths.QUICK_STATE.read_text())
    assert latest['run_id'] == 'newer_owner'
    assert latest['execution_result'] == {'run_id': 'newer_owner', 'passed': 7}


def test_admission_stays_reserved_until_surviving_children_exit(isolated):
    code = ('import subprocess,sys; '
            'subprocess.Popen([sys.executable,"-c","import time; time.sleep(.5)"])')
    launched = dash_procs.start_execution([sys.executable, '-c', code], 'run_quick')
    dash_procs._SPAWNED_PROCS[launched['pid']].wait(timeout=3)
    assert dash_procs.execution_status()['status'] == 'running'
    blocked = dash_procs.start_execution([sys.executable, '-c', 'pass'], 'run_qa')
    assert blocked['ok'] is False
    time.sleep(.6)
    assert dash_procs.execution_status()['status'] == 'interrupted'


def test_new_launch_clears_old_results_and_healing_context_without_losing_configuration(isolated):
    _paths.update_state(_paths.QUICK_STATE, lambda state: {
        'run_id': 'old', 'workflow_status': 'failed', 'execution_result': {'run_id': 'old'},
        'error': 'stale', 'heal_subagent_contexts': [{'old': True}], 'heal_count': 2,
        'generated_file_path': 'tests/generated/login', 'url': 'https://example.test',
    })
    launched = dash_procs.start_execution([sys.executable, '-c', 'import time; time.sleep(30)'], 'run_quick')
    latest = json.loads(_paths.QUICK_STATE.read_text())
    assert latest['run_id'] == launched['run_id']
    assert latest['workflow_status'] == 'running'
    assert not {'execution_result', 'error', 'heal_subagent_contexts'} & latest.keys()
    assert latest['heal_count'] == 2
    assert latest['generated_file_path'] == 'tests/generated/login'
    assert latest['url'] == 'https://example.test'
