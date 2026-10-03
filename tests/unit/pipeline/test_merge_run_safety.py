"""Merge failures remain owned and recorded even without an HTML report."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
for folder in (ROOT / 'scripts', ROOT / 'parallel'):
    sys.path.insert(0, str(folder))
spec = importlib.util.spec_from_file_location('merge_run_safety', ROOT / 'parallel/99_merge.py')
merge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge)


@pytest.fixture
def scope(tmp_path, monkeypatch):
    import _paths
    for name, path in {
        'PROJECT_ROOT': tmp_path,
        'QUICK_STATE': tmp_path / 'state/quick.json',
        'PARALLEL_STATE': tmp_path / 'state/parallel.json',
        'HEAL_CONTEXT_STATE': tmp_path / 'state/heal_context.json',
        'GENERATED_DIR': tmp_path / 'tests/generated',
        'SCREENSHOTS_DIR': tmp_path / 'tests/screenshots',
        'TRACES_DIR': tmp_path / 'tests/traces',
    }.items():
        monkeypatch.setattr(merge, name, path)
        if hasattr(_paths, name): monkeypatch.setattr(_paths, name, path)
    monkeypatch.setattr(merge, 'is_spa_group', lambda _: False)
    monkeypatch.setattr(sys, 'argv', ['99_merge.py', '--quick', '--no-report', '--group', 'login'])
    monkeypatch.setenv('QA_RUN_ID', 'run-owned')
    records = []
    monkeypatch.setattr(merge, 'append_run_history', records.append)
    target = merge.GENERATED_DIR / 'login/tc_01_login.py'
    target.parent.mkdir(parents=True)
    target.write_text('def test_login(): pass')
    monkeypatch.setattr(merge, 'collect_test_files', lambda _: ([target], 'login'))
    return records


def test_no_report_failure_has_durable_owned_result(scope, monkeypatch):
    monkeypatch.setattr(merge, 'run_pytest', lambda *args, **kwargs: (5, {}))
    try: merge.main()
    except SystemExit: pass
    assert len(scope) == 1
    assert scope[0]['run_id'] == 'run-owned'
    assert scope[0]['status'] == 'failed'
    assert scope[0]['report_path'] is None
    assert scope[0]['first_pass'] is False
    assert scope[0]['recovery']['category'] == 'configuration'
    owned = json.loads((merge.PROJECT_ROOT / 'state/runs/run-owned/execution_result.json').read_text())
    assert owned['status'] == 'failed'
    assert owned['report_path'] is None


def test_empty_test_selection_records_failure(scope, monkeypatch):
    monkeypatch.setattr(merge, 'collect_test_files', lambda _: ([], 'login'))
    merge.main()
    assert len(scope) == 1
    assert scope[0]['status'] == 'failed'
    assert scope[0]['recovery']['category'] == 'configuration'


def test_stale_merge_cannot_execute_or_overwrite_new_owner(scope, monkeypatch):
    merge.QUICK_STATE.parent.mkdir(parents=True, exist_ok=True)
    original = {'status': 'testing', 'run_id': 'newer-run', 'execution_result': {'passed': 9}}
    merge.QUICK_STATE.write_text(json.dumps(original))
    def forbidden(*args, **kwargs): pytest.fail('stale execution reached pytest')
    monkeypatch.setattr(merge, 'run_pytest', forbidden)
    merge.main()
    assert json.loads(merge.QUICK_STATE.read_text()) == original


def test_configuration_error_does_not_start_healing(scope, monkeypatch):
    report = {'summary': {'total': 0, 'failed': 0}, 'collectors': [
        {'nodeid': 'tests/generated/login/tc_01_login.py', 'outcome': 'failed',
         'longrepr': 'SyntaxError: invalid syntax'}], 'tests': []}
    monkeypatch.setattr(merge, 'run_pytest', lambda *args, **kwargs: (2, report))
    def forbidden(*args, **kwargs): pytest.fail('configuration failure attempted healing')
    monkeypatch.setattr(merge, 'run_heal_cycle', forbidden)
    merge.main()
    assert scope[0]['status'] == 'failed'
    assert scope[0]['errors'][0]['phase'] == 'collection'
    assert scope[0]['recovery']['category'] == 'configuration'


def test_parallel_report_uses_only_this_invocations_evidence(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('report_evidence_safety', ROOT / 'parallel/_report.py')
    report_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(report_module)
    monkeypatch.setattr(report_module, 'SCREENSHOTS_DIR', tmp_path)
    for owner, invocation, url in [('old', 'old-attempt', 'https://old.example'), ('run-owned', 'new-attempt', 'https://current.example')]:
        (tmp_path / f'{owner}.meta.json').write_text(json.dumps({
            'test_name': 'test_login', 'run_id': owner, 'invocation_id': invocation, 'url': url,
        }))
    collected = report_module._scan_meta_files('run-owned', 'new-attempt')
    assert collected['test_login']['url'] == 'https://current.example'
    assert report_module._scan_meta_files('run-owned', 'missing') == {}


def test_healing_receives_measured_owned_invocation(scope, monkeypatch):
    report = {'summary': {'total': 1, 'failed': 1}, '_qa_execution': {'run_id': 'run-owned', 'invocation_id': 'current-attempt'},
              'tests': [{'nodeid': 'tests/generated/login/tc_01_login.py::test_login', 'outcome': 'failed',
                         'call': {'outcome': 'failed', 'longrepr': 'Error: strict mode violation: locator("button") resolved to 2 elements'}}]}
    monkeypatch.setattr(merge, 'run_pytest', lambda *args, **kwargs: (1, report))
    def heal(*args, **kwargs):
        state = merge.read_state(merge.QUICK_STATE)
        assert state['execution_result']['run_id'] == 'run-owned'
        assert state['execution_result']['invocation_id'] == 'current-attempt'
        assert state['execution_result']['failed'] == 1
        return False, True, False
    monkeypatch.setattr(merge, 'run_heal_cycle', heal)
    merge.main()
    assert scope[0]['status'] == 'failed'
    assert scope[0]['report_path'] is None
    assert not list((merge.PROJECT_ROOT / 'tests/reports').glob('*.html'))


@pytest.mark.parametrize('exit_code,category,status', [(0, 'unknown', 'failed'), (1, 'unknown', 'failed'), (2, 'interrupted', 'interrupted'), (-15, 'interrupted', 'interrupted')])
def test_metadata_only_report_cannot_be_passed(scope, monkeypatch, exit_code, category, status):
    monkeypatch.setattr(merge, 'run_pytest', lambda *args, **kwargs: (exit_code, {
        '_qa_execution': {'run_id': 'run-owned', 'invocation_id': 'missing-report'},
    }))
    def forbidden(*args, **kwargs): pytest.fail('unmeasured run attempted healing')
    monkeypatch.setattr(merge, 'run_heal_cycle', forbidden)
    try: merge.main()
    except SystemExit: pass
    assert len(scope) == 1
    assert scope[0]['status'] == status
    assert scope[0]['total'] == 0 and not scope[0]['first_pass']
    assert scope[0]['recovery']['category'] == category
    assert not scope[0]['recovery']['can_heal']


@pytest.mark.parametrize('terminal', ['cancelled', 'interrupted', 'timed_out'])
def test_terminal_owner_never_reaches_pytest(scope, monkeypatch, terminal):
    from run_results import write_execution_result
    write_execution_result(merge.PROJECT_ROOT, 'run-owned', {'status': terminal})
    def forbidden(*args, **kwargs): pytest.fail('terminal owner replayed test actions')
    monkeypatch.setattr(merge, 'run_pytest', forbidden)
    merge.main()
    assert scope == []


@pytest.mark.parametrize('exit_code', [2, -15])
def test_partial_locator_failure_has_interrupted_status(scope, monkeypatch, exit_code):
    report = {'summary': {'total': 1, 'failed': 1}, 'tests': [{
        'nodeid': 'tests/generated/login/tc_01_login.py::test_login', 'outcome': 'failed',
        'call': {'outcome': 'failed', 'longrepr': 'Error: strict mode violation: locator("button") resolved to 2 elements'},
    }]}
    monkeypatch.setattr(merge, 'run_pytest', lambda *args, **kwargs: (exit_code, report))
    def forbidden(*args, **kwargs): pytest.fail('interrupted run attempted healing')
    monkeypatch.setattr(merge, 'run_heal_cycle', forbidden)
    merge.main()
    assert scope[0]['status'] == 'interrupted'
    assert scope[0]['recovery']['category'] == 'interrupted'


def test_missing_verifier_measurements_cannot_finish_heal_as_passed(scope, monkeypatch):
    locator = {'summary': {'total': 1, 'failed': 1}, 'tests': [{
        'nodeid': 'tests/generated/login/tc_01_login.py::test_login', 'outcome': 'failed',
        'call': {'outcome': 'failed', 'longrepr': 'Error: strict mode violation: locator("button") resolved to 2 elements'},
    }]}
    invocations = []
    def run(*args, **kwargs):
        invocations.append(True)
        return (1, locator) if len(invocations) == 1 else (0, {'_qa_execution': {'invocation_id': 'empty-verifier'}})
    monkeypatch.setattr(merge, 'run_pytest', run)
    monkeypatch.setattr(merge, 'run_heal_cycle', lambda *args: (True, False, True))
    merge.main()
    assert len(invocations) == 2
    assert scope[0]['status'] == 'failed' and not scope[0]['first_pass']
    assert scope[0]['recovery']['category'] == 'unknown'
    assert not scope[0]['recovery']['can_heal']
