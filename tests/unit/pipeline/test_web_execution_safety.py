"""Web recovery must classify failures without replaying test actions."""
import asyncio
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))


def load_script(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def policy():
    assert (ROOT / 'scripts/error_policy.py').exists(), 'web error policy is missing'
    return load_script('web_policy_test', 'scripts/error_policy.py')


@pytest.mark.parametrize('error,category,heal,retry', [
    ('BrowserType.launch: Executable doesn\'t exist at /tmp/chromium', 'browser_unavailable', False, False),
    ('TargetClosedError: Target page, context or browser has been closed', 'session_lost', False, False),
    ('Error: net::ERR_CONNECTION_RESET', 'transport', False, True),
    ('Error: net::ERR_CONNECTION_REFUSED', 'transport', False, False),
    ('TimeoutError: Locator.click: Timeout 30000ms exceeded. waiting for locator("#submit")', 'locator', True, False),
    ('Error: strict mode violation: locator("button") resolved to 2 elements', 'locator', True, False),
    ('AssertionError: Locator expected to be visible', 'assertion', False, False),
    ('TimeoutError: Page.goto: Timeout 30000ms exceeded', 'timeout', False, False),
    ('SyntaxError: invalid syntax', 'configuration', False, False),
    ('unexpected application error', 'unknown', False, False),
])
def test_classifies_web_failure_without_action_replay(error, category, heal, retry):
    result = policy().classify_error(error)
    assert (result['category'], result['can_heal'], result['read_retryable']) == (category, heal, retry)
    assert result['title'] and result['message'] and result['action']
    assert 'Appium' not in result['message'] and '기기' not in result['message']


def test_mixed_failures_block_locator_healing():
    result = {'execution_result': {'group_results': {'demo': {'tests': [
        {'outcome': 'failed', 'error': 'strict mode violation: locator resolved to 2 elements'},
        {'outcome': 'failed', 'error': 'AssertionError: expected success'},
        {'outcome': 'passed', 'error': ''},
    ]}}}}
    assert policy().recovery_for_result(result)['category'] == 'assertion'
    assert not policy().recovery_for_result(result)['can_heal']


def test_locator_error_without_failed_test_cannot_heal():
    result = {'status': 'failed', 'error': 'strict mode violation: locator resolved to 2 elements'}
    assert not policy().recovery_for_result(result)['can_heal']


@pytest.mark.parametrize('status,category', [('timed_out', 'timeout'), ('interrupted', 'interrupted')])
def test_terminal_status_overrides_locator_symptoms(status, category):
    assert policy().recovery_for_result({'status': status})['category'] == category


@pytest.mark.parametrize('failures,expected_calls,raises', [(2, 3, False), (4, 3, True)])
def test_dom_read_retry_is_bounded(failures, expected_calls, raises):
    analyze = load_script('safe_analyze', 'scripts/01_analyze.py')
    assert hasattr(analyze, '_read_dom'), 'bounded DOM read helper is missing'
    class Page:
        calls = 0
        async def evaluate(self, script):
            assert script == analyze.DOM_EXTRACT_JS
            self.calls += 1
            if self.calls <= failures:
                raise OSError('connection reset')
            return {'title': 'read-only DOM'}
    page = Page()
    if raises:
        with pytest.raises(OSError, match='connection reset'):
            asyncio.run(analyze._read_dom(page, analyze.DOM_EXTRACT_JS))
    else:
        assert asyncio.run(analyze._read_dom(page, analyze.DOM_EXTRACT_JS)) == {'title': 'read-only DOM'}
    assert page.calls == expected_calls


def test_dom_read_does_not_retry_unknown_errors():
    analyze = load_script('safe_analyze_unknown', 'scripts/01_analyze.py')
    assert hasattr(analyze, '_read_dom'), 'bounded DOM read helper is missing'
    class Page:
        calls = 0
        async def evaluate(self, script):
            self.calls += 1
            raise RuntimeError('unexpected application error')
    page = Page()
    with pytest.raises(RuntimeError):
        asyncio.run(analyze._read_dom(page, analyze.DOM_EXTRACT_JS))
    assert page.calls == 1


@pytest.mark.parametrize('long_command', [False, True])
def test_parallel_pytest_disables_rerun_plugin(monkeypatch, tmp_path, long_command):
    execute = load_script('safe_parallel_exec', 'parallel/_exec.py')
    monkeypatch.setattr(execute, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(execute.tempfile, 'gettempdir', lambda: str(tmp_path))
    observed = []
    def run(cmd, **kwargs):
        if long_command:
            namespace = {'__name__': '__test_runner__'}
            import pytest as pytest_module
            monkeypatch.setattr(pytest_module, 'main', lambda args: observed.append(args) or 1)
            with pytest.raises(SystemExit):
                exec(Path(cmd[1]).read_text(), namespace)
        else:
            observed.append(cmd)
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(execute.subprocess, 'run', run)
    paths = [Path('x' * (21000 if long_command else 20))]
    code, _ = execute.run_pytest(paths, single_session=True)
    assert code == 1 and len(observed) == 1
    assert ['-p', 'no:rerunfailures'] == observed[0][observed[0].index('-p'):observed[0].index('-p') + 2]


@pytest.mark.parametrize("newer_run,process_error", [(False, None), (True, None), (False, "timeout"), (False, "interrupted"), (False, "launch")])
def test_single_execution_persists_recovery_and_disables_reruns(monkeypatch, tmp_path, newer_run, process_error):
    execute = load_script('safe_single_exec', 'scripts/05_execute.py')
    test_file = tmp_path / 'tc_01_sample.py'
    test_file.write_text('def test_sample():\n    assert False\n')
    state = {'step': 'reviewed', 'generated_file_path': str(test_file), 'group_dir': 'demo'}
    monkeypatch.setattr(execute, 'PIPELINE_STATE', tmp_path / 'pipeline.json')
    execute.PIPELINE_STATE.touch()
    monkeypatch.setattr(execute, 'PROJECT_ROOT', tmp_path)
    for field in ['SCREENSHOTS_DIR', 'TRACES_DIR']:
        monkeypatch.setattr(execute, field, tmp_path / field)
    monkeypatch.setattr(execute, 'read_state', lambda _: dict(state))
    monkeypatch.setattr(execute, 'update_state', lambda _, mutator: state.update(mutator(dict(state))))
    monkeypatch.setattr(execute, 'is_spa_group', lambda _: False)
    monkeypatch.setattr(execute, '_load_cases_for_group', lambda _: [])
    monkeypatch.setattr(execute, 'slog', lambda *a, **k: None)
    history = []
    monkeypatch.setattr(execute, 'append_run_history', history.append)
    commands = []
    def run(cmd, **kwargs):
        if newer_run:
            state.update(last_run_id="run_newer", execution_result={"run_id": "run_newer", "status": "running"})
        commands.append(cmd)
        if process_error == "timeout":
            raise subprocess.TimeoutExpired(cmd, 3600)
        if process_error == "interrupted":
            raise KeyboardInterrupt
        if process_error == "launch":
            raise FileNotFoundError("python executable missing")
        report_file = next(a.split('=', 1)[1] for a in cmd if a.startswith('--json-report-file='))
        Path(report_file).write_text(json.dumps({'summary': {'failed': 1}, 'tests': [{
            'nodeid': 'demo/tc_01_sample.py::test_sample', 'outcome': 'failed',
            'call': {'outcome': 'failed', 'longrepr': 'AssertionError: expected success'},
        }]}))
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(execute.subprocess, 'run', run)
    monkeypatch.setattr(sys, 'argv', ['05_execute.py', '--no-report'])
    if process_error:
        with pytest.raises(SystemExit):
            execute.main()
    else:
        execute.main()
    assert len(commands) == 1
    assert '-p' in commands[0] and 'no:rerunfailures' in commands[0]
    expected_category = {"timeout": "timeout", "interrupted": "interrupted", "launch": "configuration"}.get(process_error, "assertion")
    if newer_run:
        assert state["execution_result"] == {"run_id": "run_newer", "status": "running"}
    else:
        assert state['execution_result']['recovery']['category'] == expected_category
    assert history[0]['recovery']['category'] == expected_category
    assert history[0]['status'] == {"timeout": "timed_out", "interrupted": "interrupted"}.get(process_error, "failed")
    if not newer_run:
        assert history[0]['run_id'] == state['execution_result']['run_id']
    from run_results import read_execution_result
    assert read_execution_result(tmp_path, history[0]["run_id"])["recovery"]["category"] == expected_category


def test_teardown_blocker_overrides_call_locator_error():
    report = {'tests': [{'nodeid': 'demo::test_one', 'outcome': 'failed',
        'call': {'outcome': 'failed', 'longrepr': 'Error: strict mode violation: locator resolved to 2 elements'},
        'teardown': {'outcome': 'failed', 'longrepr': 'TargetClosedError: Target page, context or browser has been closed'},
    }]}
    module = policy()
    assert hasattr(module, 'errors_from_report'), 'phase error extraction is missing'
    errors = module.errors_from_report(report)
    assert len(errors) == 2
    assert module.recovery_for_result({'errors': errors})['category'] == 'session_lost'


def test_collection_errors_are_configuration_failures():
    module = policy()
    assert hasattr(module, 'errors_from_report'), 'phase error extraction is missing'
    errors = module.errors_from_report({'collectors': [{'nodeid': 'demo.py', 'outcome': 'failed', 'longrepr': 'collecting failed'}]})
    assert module.recovery_for_result({'errors': errors})['category'] == 'configuration'


def test_run_results_are_owned_and_atomically_persisted(tmp_path):
    assert (ROOT / 'scripts/run_results.py').exists(), 'run-owned persistence is missing'
    module = load_script('safe_run_results', 'scripts/run_results.py')
    module.write_execution_result(tmp_path, 'run_one', {'status': 'failed', 'errors': [{'error': 'AssertionError'}]})
    module.write_execution_result(tmp_path, 'run_two', {'status': 'passed'})
    assert module.read_execution_result(tmp_path, 'run_one')['status'] == 'failed'
    assert module.read_execution_result(tmp_path, 'run_two')['status'] == 'passed'
    assert module.read_execution_result(tmp_path, 'run_missing') is None
    with pytest.raises(ValueError):
        module.write_execution_result(tmp_path, '../escape', {})
    with pytest.raises(ValueError):
        module.write_execution_result(tmp_path, 'run_one', {'run_id': 'run_two'})
    assert not list(tmp_path.rglob('*.tmp'))


def test_missing_test_file_records_run_owned_failure(monkeypatch, tmp_path):
    execute = load_script('safe_startup_exec', 'scripts/05_execute.py')
    state_path = tmp_path / 'pipeline.json'
    state_path.write_text(json.dumps({'step': 'reviewed', 'generated_file_path': str(tmp_path / 'absent.py')}))
    monkeypatch.setattr(execute, 'PIPELINE_STATE', state_path)
    monkeypatch.setattr(execute, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(execute, 'append_run_history', lambda row: history.append(row))
    monkeypatch.setenv('QA_RUN_ID', 'run_startup')
    monkeypatch.setattr(sys, 'argv', ['05_execute.py', '--no-report'])
    history = []
    with pytest.raises(SystemExit):
        execute.main()
    from run_results import read_execution_result
    owned = read_execution_result(tmp_path, 'run_startup')
    assert owned and owned['status'] == 'failed'
    assert owned['recovery']['category'] == 'configuration'
    assert history[0]['run_id'] == 'run_startup'


def test_custom_state_uses_worker_owned_run_id(monkeypatch, tmp_path):
    execute = load_script('safe_worker_exec', 'scripts/05_execute.py')
    path = tmp_path / 'workers' / 'demo.json'
    path.parent.mkdir()
    path.write_text(json.dumps({'step': 'reviewed', 'generated_file_path': str(tmp_path / 'absent.py')}))
    monkeypatch.setattr(execute, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setenv('QA_RUN_ID', 'root_workflow')
    monkeypatch.setenv('QA_WORKFLOW_ID', 'root_workflow')
    history = []
    monkeypatch.setattr(execute, 'append_run_history', history.append)
    monkeypatch.setattr(sys, 'argv', ['05_execute.py', '--no-report', '--state-path', str(path)])
    with pytest.raises(SystemExit):
        execute.main()
    assert history and history[0]['run_id'] != 'root_workflow'
    assert history[0]['workflow_id'] == 'root_workflow'
    from run_results import read_execution_result
    assert read_execution_result(tmp_path, 'root_workflow') is None


def test_pytest_artifacts_use_owned_prefix(tmp_path):
    import os
    (tmp_path / 'test_artifact.py').write_text('''from pathlib import Path
import pytest
class Tracing:
    def stop(self, path=None):
        if path:
            Path(path).write_bytes(b"trace")
class Page:
    url = "https://example.test"
    context = type("Context", (), {"tracing": Tracing()})()
    def screenshot(self, path):
        Path(path).write_bytes(b"screenshot")
@pytest.fixture
def page():
    return Page()
def test_failure(page):
    assert False
''')
    result = subprocess.run([sys.executable, '-m', 'pytest', '-p', 'tests.conftest', '-q', 'test_artifact.py'],
                            cwd=tmp_path, capture_output=True, text=True,
                            env={**os.environ, 'PYTHONPATH': str(ROOT), 'QA_ARTIFACT_PREFIX': 'run_owned__attempt_one__',
                                 'QA_RUN_ID': 'run_owned', 'QA_INVOCATION_ID': 'attempt_one'})
    assert result.returncode == 1, result.stdout + result.stderr
    path = tmp_path / f'tests/screenshots/run_owned__attempt_one__{tmp_path.name}__test_failure.meta.json'
    assert path.exists(), 'failure artifacts did not receive their owner prefix'
    metadata = json.loads(path.read_text())
    assert metadata['run_id'] == 'run_owned' and metadata['invocation_id'] == 'attempt_one'
    assert Path(tmp_path / metadata['screenshot_path']).exists()
    assert Path(tmp_path / metadata['trace_path']).exists()


def test_late_execution_result_cannot_replace_cancelled_owner(tmp_path):
    module = load_script('safe_terminal_results', 'scripts/run_results.py')
    module.write_execution_result(tmp_path, 'run_cancel', {'status': 'running'})
    module.write_execution_result(tmp_path, 'run_cancel', {'status': 'cancelled', 'finished_at': 'original'})
    returned = module.write_execution_result(tmp_path, 'run_cancel', {'status': 'passed', 'finished_at': 'late'})
    assert returned['status'] == 'cancelled'
    assert module.read_execution_result(tmp_path, 'run_cancel')['finished_at'] == 'original'


@pytest.mark.parametrize('exit_code,collection,category', [
    (2, False, 'interrupted'), (2, True, 'configuration'),
    (3, False, 'unknown'), (4, False, 'configuration'), (5, False, 'configuration'),
    (-15, False, 'interrupted'), (-9, False, 'interrupted'),
])
def test_abnormal_pytest_exit_blocks_partial_locator_healing(exit_code, collection, category):
    errors = [{'nodeid': 'demo::test_partial', 'error': 'strict mode violation: locator resolved to 2 elements'}]
    if collection:
        errors.append({'phase': 'collection', 'error_type': 'CollectionError', 'error': 'collection failed'})
    result = {'status': 'failed', 'exit_code': exit_code, 'errors': errors}
    recovery = policy().recovery_for_result(result)
    assert recovery['category'] == category
    assert not recovery['can_heal'] and not recovery['read_retryable']
