"""Recovery verification is a single attempt with rollback and fresh evidence."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / 'scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def recovery(tmp_path, monkeypatch):
    heal = load('06_auto_heal')
    files = [tmp_path / f'tc_{i}.py' for i in range(2)]
    originals = {}
    for file in files:
        originals[file] = b'def test_x(page):\r\n    page.locator(".a").click()\r\n'
        file.write_bytes(originals[file])
    context = {'url': 'https://example.test', 'failures': [
        {'test_id': f'{file}::test_x', 'test_name': 'test_x',
         'traceback': 'strict mode violation locator(".a")'} for file in files]}
    state = tmp_path / 'state.json'
    state.write_text(json.dumps({'step': 'heal_needed', 'heal_context': context}))
    monkeypatch.setattr(sys, 'argv', ['06_auto_heal.py', '--state-path', str(state)])
    # Browser acquisition is the external boundary; fixture supplies current evidence.
    monkeypatch.setattr(heal, '_refresh_heal_snapshot', lambda *a: {'https://example.test': {'buttons': []}}, raising=False)
    return heal, files, originals, state


@pytest.mark.parametrize('result', [
    SimpleNamespace(returncode=1, stdout='test_x FAILED', stderr=''),
    SimpleNamespace(returncode=2, stdout='collection failed', stderr=''),
    SimpleNamespace(returncode=1, stdout='test_x PASSED\ntest_y PASSED\nteardown ERROR', stderr=''),
    subprocess.TimeoutExpired('pytest', 300),
    OSError('cannot launch pytest'),
])
def test_failed_verification_restores_original_bytes_and_stops(recovery, monkeypatch, result):
    heal, files, originals, state = recovery
    calls = []
    def execute(command, **kwargs):
        calls.append(command)
        if isinstance(result, Exception):
            raise result
        return result
    monkeypatch.setattr(heal.subprocess, 'run', execute)
    with pytest.raises(SystemExit) as stopped:
        heal.main()
    assert stopped.value.code == 5
    assert len(calls) == 1
    assert '-p' in calls[0] and 'no:rerunfailures' in calls[0]
    assert {file: file.read_bytes() for file in files} == originals
    saved = json.loads(state.read_text())
    assert saved['heal_context']['recovery_stopped'] is True
    assert saved['step'] == 'heal_failed'
    assert len(saved['heal_context']['failures']) == 2


def test_failed_refresh_does_not_patch_or_verify(recovery, monkeypatch):
    heal, files, originals, state = recovery
    def failed(*args):
        raise RuntimeError('fresh DOM unavailable')
    monkeypatch.setattr(heal, '_refresh_heal_snapshot', failed, raising=False)
    monkeypatch.setattr(heal.subprocess, 'run', lambda *a, **k: pytest.fail('must not execute'))
    with pytest.raises(SystemExit) as stopped:
        heal.main()
    assert stopped.value.code == 5
    assert {file: file.read_bytes() for file in files} == originals


def test_nonzero_exit_cannot_count_as_all_passed():
    assert not load('06_auto_heal')._rerun_outcome('test_x PASSED', 1, 1)['all_passed']


def test_single_failure_collection_never_reexecutes_missing_report(monkeypatch):
    heal = load('06_heal')
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: pytest.fail('diagnostics must not replay test actions'))
    failures, _ = heal.collect_failure_details_from_report({'execution_result': {'output': 'original failure'}})
    assert failures == []


def test_refresh_uses_only_new_pages_and_disables_cached_interactions(monkeypatch):
    import heal_utils
    seen = []
    async def analyze(url, sub_urls, **kwargs):
        seen.append((url, sub_urls, kwargs))
        return {'url': url, 'buttons': []}, {}
    analyzer = SimpleNamespace(analyze_all=analyze)
    monkeypatch.setattr(importlib.util, 'spec_from_file_location', lambda *a: SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _: None)))
    monkeypatch.setattr(importlib.util, 'module_from_spec', lambda _: analyzer)
    stale = {'dom_info': {'old': 'stale'}, 'url': 'https://new.test'}
    snapshot = heal_utils.refresh_heal_snapshot({}, stale)
    assert snapshot == {'https://new.test': {'url': 'https://new.test', 'buttons': []}}
    assert seen == [('https://new.test', [], {'force_refresh': True, 'skip_dynamic': True})]
    assert stale['dom_info'] == {'old': 'stale'}


def test_refresh_error_never_returns_partial_or_stale_pages(monkeypatch):
    import heal_utils
    async def analyze(url, *args, **kwargs):
        return ({'buttons': []} if url.endswith('a.test') else {'error': 'browser lost'}), {}
    monkeypatch.setattr(importlib.util, 'spec_from_file_location', lambda *a: SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _: None)))
    monkeypatch.setattr(importlib.util, 'module_from_spec', lambda _: SimpleNamespace(analyze_all=analyze))
    with pytest.raises(RuntimeError, match='browser lost'):
        heal_utils.refresh_heal_snapshot({'urls': {'a': 'https://a.test', 'b': 'https://b.test'}}, {'dom_info': {'old': 'stale'}})


def test_parallel_stopped_recovery_never_prints_agent_work(tmp_path, monkeypatch):
    from parallel import _healer as healer
    context_path = tmp_path / 'heal.json'
    context_path.write_text(json.dumps({'recovery_stopped': True, 'failures': [{'test_name': 'test_x'}]}))
    monkeypatch.setattr(healer, 'HEAL_CONTEXT_STATE', context_path)
    monkeypatch.setattr(healer, '_build_heal_context', lambda *a: {'failures': [{'test_name': 'test_x'}]})
    monkeypatch.setattr(healer, '_try_auto_heal', lambda **k: False)
    monkeypatch.setattr(healer, 'print_heal_instructions', lambda *a, **k: pytest.fail('must not start another strategy'))
    assert healer.run_heal_cycle({}, 1, tmp_path / 'parallel.json', False) == (False, True, False)


@pytest.mark.parametrize('traceback', ['AssertionError: expected saved', 'TargetClosedError: browser disconnected', 'TimeoutError: operation timed out', 'unknown exception'])
def test_unsafe_failure_never_refreshes_or_executes(recovery, monkeypatch, traceback):
    heal, files, originals, state = recovery
    saved = json.loads(state.read_text())
    saved['heal_context']['failures'][0]['traceback'] = traceback
    state.write_text(json.dumps(saved))
    monkeypatch.setattr(heal, '_refresh_heal_snapshot', lambda *a: pytest.fail('unsafe failure must not refresh'))
    monkeypatch.setattr(heal.subprocess, 'run', lambda *a, **k: pytest.fail('unsafe failure must not execute'))
    with pytest.raises(SystemExit) as stopped:
        heal.main()
    assert stopped.value.code == 5
    assert {file: file.read_bytes() for file in files} == originals


def test_single_unsafe_failure_stops_before_site_probe(tmp_path, monkeypatch):
    heal = load('06_heal')
    state_path = tmp_path / 'pipeline.json'
    state_path.write_text(json.dumps({'step': 'reviewed', 'url': 'https://example.test',
                                     'execution_result': {'failed': 1, 'exit_code': 1}}))
    monkeypatch.setattr(heal, 'PIPELINE_STATE', state_path)
    monkeypatch.setattr(heal, 'collect_failure_details_from_report', lambda _: ([{'test_id': 't.py::test_x', 'test_name': 'test_x', 'traceback': 'AssertionError: expected saved'}], ''))
    import urllib.request
    monkeypatch.setattr(urllib.request, 'urlopen', lambda *a, **k: pytest.fail('must not probe or heal'))
    with pytest.raises(SystemExit) as stopped:
        heal.main()
    assert stopped.value.code == 2
    saved = json.loads(state_path.read_text())
    assert saved['step'] == 'heal_failed'
    assert saved['heal_context']['recovery']['category'] == 'assertion'


def test_interrupted_verification_restores_original_files(recovery, monkeypatch):
    heal, files, originals, _ = recovery
    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt()
    monkeypatch.setattr(heal.subprocess, 'run', interrupted)
    with pytest.raises(KeyboardInterrupt):
        heal.main()
    assert {file: file.read_bytes() for file in files} == originals


def test_sigterm_verification_unwinds_original_files(recovery, monkeypatch):
    import os
    import signal
    heal, files, originals, _ = recovery
    previous = signal.getsignal(signal.SIGTERM)
    def interrupted(*args, **kwargs):
        os.kill(os.getpid(), signal.SIGTERM)
        pytest.fail('SIGTERM must interrupt verification')
    monkeypatch.setattr(heal.subprocess, 'run', interrupted)
    with pytest.raises(SystemExit) as stopped:
        heal.main()
    assert stopped.value.code == 143
    assert {file: file.read_bytes() for file in files} == originals
    assert signal.getsignal(signal.SIGTERM) == previous


def test_assert_guard_reads_requested_state_path(tmp_path, monkeypatch):
    guard = load('assert_guard')
    state_path = tmp_path / 'parallel.json'
    state_path.write_text(json.dumps({'pre_heal_assertions': {'test.py': {'strong': [], 'weak': []}}}))
    monkeypatch.setattr(guard, 'PIPELINE_STATE', tmp_path / 'absent.json')
    monkeypatch.setattr(sys, 'argv', ['assert_guard.py', '--state-path', str(state_path)])
    monkeypatch.setattr(guard, 'snapshot_assertions', lambda _: {})
    monkeypatch.setattr(guard, 'compare_assertions', lambda *a: {'has_warnings': False, 'warnings': []})
    with pytest.raises(SystemExit) as complete:
        guard.main()
    assert complete.value.code == 0
    assert 'assertion_integrity' in json.loads(state_path.read_text())


def test_healing_reads_owned_result_without_using_latest_summary(tmp_path, monkeypatch):
    import heal_utils
    from run_results import write_execution_result
    monkeypatch.setenv('QA_RUN_ID', 'owned')
    owned = write_execution_result(tmp_path, 'owned', {'exit_code': 1, 'errors': [{'nodeid': 'owned.py::test_x', 'error': 'strict mode violation'}]})
    state = {'last_run_id': 'owned', 'execution_result': {'errors': [{'nodeid': 'stale.py::test_x'}]}}
    loaded = heal_utils.load_heal_execution_state(state, tmp_path)
    assert loaded['execution_result'] == owned
    assert state['execution_result']['errors'][0]['nodeid'] == 'stale.py::test_x'


@pytest.mark.parametrize('owner', ['newer', 'owned'])
def test_healing_refuses_missing_result_or_superseded_run(tmp_path, monkeypatch, owner):
    import heal_utils
    monkeypatch.setenv('QA_RUN_ID', 'owned')
    with pytest.raises(RuntimeError):
        heal_utils.load_heal_execution_state({'last_run_id': owner, 'execution_result': {'errors': []}}, tmp_path)


def test_recovery_state_update_preserves_newer_run(tmp_path, monkeypatch):
    import heal_utils
    monkeypatch.setenv('QA_RUN_ID', 'old')
    state_path = tmp_path / 'pipeline.json'
    current = {'last_run_id': 'new', 'step': 'reviewed', 'heal_count': 3}
    state_path.write_text(json.dumps(current))
    heal_utils.update_heal_state(state_path, lambda fresh: {**fresh, 'step': 'heal_failed'})
    assert json.loads(state_path.read_text()) == current


def test_parallel_autoheal_launch_error_marks_terminal_recovery(tmp_path, monkeypatch):
    from parallel import _healer as healer
    context_path = tmp_path / 'heal.json'
    context_path.write_text(json.dumps({'failures': [{'test_name': 'test_x'}]}))
    monkeypatch.setattr(healer, 'HEAL_CONTEXT_STATE', context_path)
    def unavailable(*args, **kwargs):
        raise OSError('cannot launch interpreter')
    monkeypatch.setattr(healer.subprocess, 'run', unavailable)
    assert healer._try_auto_heal(tmp_path / 'parallel.json') is False
    assert json.loads(context_path.read_text())['recovery_stopped'] is True


def test_healing_worker_reads_same_derived_owner_as_execution(tmp_path, monkeypatch):
    import heal_utils
    from run_results import worker_run_id, write_execution_result
    monkeypatch.setenv('QA_RUN_ID', 'workflow')
    state_path = tmp_path / 'worker.json'
    owner = worker_run_id('workflow', state_path)
    owned = write_execution_result(tmp_path, owner, {'exit_code': 1, 'errors': []})
    loaded = heal_utils.load_heal_execution_state({'last_run_id': owner}, tmp_path, state_path=state_path)
    assert loaded['execution_result'] == owned


def test_single_healer_accepts_worker_state_path(tmp_path, monkeypatch):
    heal = load('06_heal')
    state_path = tmp_path / 'worker.json'
    state_path.write_text(json.dumps({'step': 'reviewed', 'execution_result': {'failed': 1, 'exit_code': 1}}))
    monkeypatch.setattr(heal, 'PIPELINE_STATE', tmp_path / 'absent.json')
    monkeypatch.setattr(sys, 'argv', ['06_heal.py', '--state-path', str(state_path)])
    with pytest.raises(SystemExit) as stopped:
        heal.main()
    assert stopped.value.code == 2
    assert json.loads(state_path.read_text())['step'] == 'heal_failed'


def test_screenshot_lookup_matches_current_execution_only(tmp_path, monkeypatch):
    import heal_utils
    monkeypatch.setattr(heal_utils, 'SCREENSHOTS_DIR', tmp_path)
    for run, invocation in [('old', 'before'), ('owned', 'current')]:
        shot = tmp_path / f'{run}__{invocation}__group__test_x.png'
        shot.write_bytes(b'image')
        shot.with_suffix('.meta.json').write_text(json.dumps({'run_id': run, 'invocation_id': invocation}))
    result = heal_utils.find_screenshot_for_test('test_x', run_id='owned', invocation_id='current')
    assert result['path'].endswith('owned__current__group__test_x.png')
    assert heal_utils.find_screenshot_for_test('test_x', run_id='owned', invocation_id='missing') is None


def test_parallel_impossible_context_preserves_recovery_in_state(tmp_path, monkeypatch):
    from parallel import _healer as healer
    context_path = tmp_path / 'heal.json'
    context_path.write_text(json.dumps({'recovery_stopped': True, 'error': 'assertion mismatch', 'recovery': {'category': 'assertion'}}))
    state_path = tmp_path / 'parallel.json'
    state_path.write_text(json.dumps({'execution_result': {'failed': 1}, 'user_metadata': 'keep'}))
    monkeypatch.setattr(healer, 'HEAL_CONTEXT_STATE', context_path)
    monkeypatch.setattr(healer, '_build_heal_context', lambda *a: None)
    assert healer.run_heal_cycle({}, 1, state_path, False) == (False, True, False)
    saved = json.loads(state_path.read_text())
    assert saved['heal_context']['error'] == 'assertion mismatch'
    assert saved['execution_result']['recovery_stop']['category'] == 'assertion'
    assert saved['user_metadata'] == 'keep'


def test_external_heal_context_from_other_run_is_rejected(recovery, tmp_path, monkeypatch):
    heal, files, originals, state = recovery
    saved = json.loads(state.read_text())
    saved['execution_result'] = {'run_id': 'current'}
    state.write_text(json.dumps(saved))
    foreign = tmp_path / 'foreign.json'
    foreign.write_text(json.dumps({**saved['heal_context'], 'run_id': 'old'}))
    monkeypatch.setattr(heal, 'load_heal_execution_state', lambda state, **kwargs: state)
    monkeypatch.setenv('QA_RUN_ID', 'current')
    monkeypatch.setattr(sys, 'argv', ['06_auto_heal.py', '--state-path', str(state), '--heal-context-path', str(foreign)])
    monkeypatch.setattr(heal, '_refresh_heal_snapshot', lambda *a: pytest.fail('must not use foreign context'))
    with pytest.raises(SystemExit) as stopped:
        heal.main()
    assert stopped.value.code == 5
    assert {file: file.read_bytes() for file in files} == originals


def test_deliberation_respects_worker_state_and_terminal_stop(tmp_path, monkeypatch):
    dialog = load('06a_dialog')
    state_path = tmp_path / 'worker.json'
    state_path.write_text(json.dumps({'step': 'heal_needed', 'heal_context': {'recovery_stopped': True}}))
    monkeypatch.setattr(dialog, 'PIPELINE_STATE', tmp_path / 'absent.json')
    monkeypatch.setattr(sys, 'argv', ['06a_dialog.py', '--state-path', str(state_path)])
    with pytest.raises(SystemExit) as stopped:
        dialog.main()
    assert stopped.value.code == 5


def test_interruption_during_result_parsing_rolls_back_provisional_file(recovery, monkeypatch):
    heal, files, originals, _ = recovery
    monkeypatch.setattr(heal.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='test_x PASSED', stderr=''))
    def interrupted(*args):
        raise KeyboardInterrupt()
    monkeypatch.setattr(heal, '_rerun_outcome', interrupted)
    with pytest.raises(KeyboardInterrupt):
        heal.main()
    assert {file: file.read_bytes() for file in files} == originals


def test_parallel_retains_detailed_stop_cause_from_autoheal(tmp_path, monkeypatch):
    from parallel import _healer as healer
    context_path = tmp_path / 'heal.json'
    context_path.write_text(json.dumps({'recovery_stopped': True, 'error': '새 DOM 수집 실패: browser lost'}))
    monkeypatch.setattr(healer, 'HEAL_CONTEXT_STATE', context_path)
    monkeypatch.setattr(healer.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=5, stdout=''))
    assert healer._try_auto_heal(tmp_path / 'parallel.json') is False
    assert json.loads(context_path.read_text())['error'] == '새 DOM 수집 실패: browser lost'


def test_verification_artifacts_get_fresh_invocation_prefix(recovery, monkeypatch):
    heal, _, _, state = recovery
    monkeypatch.setenv('QA_INVOCATION_ID', 'old-invocation')
    monkeypatch.setenv('QA_ARTIFACT_PREFIX', 'old-prefix__')
    captured = []
    def verify(*args, **kwargs):
        captured.append(kwargs)
        return SimpleNamespace(returncode=1, stdout='test_x FAILED', stderr='')
    monkeypatch.setattr(heal.subprocess, 'run', verify)
    with pytest.raises(SystemExit) as stopped:
        heal.main()
    assert stopped.value.code == 5
    env = captured[0]['env']
    assert env['QA_INVOCATION_ID'] != 'old-invocation'
    assert env['QA_ARTIFACT_PREFIX'] == f"{env['QA_RUN_ID']}__{env['QA_INVOCATION_ID']}__"


def test_relative_pipeline_alias_uses_same_owner_as_absolute_path(tmp_path, monkeypatch):
    import _paths
    import heal_utils
    from run_results import write_execution_result
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('QA_RUN_ID', 'workflow')
    state_path = tmp_path / 'pipeline.json'
    monkeypatch.setattr(_paths, 'PIPELINE_STATE', state_path)
    owned = write_execution_result(tmp_path, 'workflow', {'exit_code': 1, 'errors': []})
    state = {'last_run_id': 'workflow'}
    state_path.write_text(json.dumps(state))
    assert heal_utils.load_heal_execution_state(state, tmp_path, state_path=Path('pipeline.json'))['execution_result'] == owned
    heal_utils.update_heal_state(Path('pipeline.json'), lambda fresh: {**fresh, 'heal_count': 1})
    assert json.loads(state_path.read_text())['heal_count'] == 1


@pytest.mark.parametrize('exit_code', [1, 2, 3, -1])
def test_single_admission_checks_all_phases_and_abnormal_exit(tmp_path, monkeypatch, exit_code):
    heal = load('06_heal')
    report = {'tests': [{'nodeid': 't.py::test_x', 'outcome': 'failed',
                         'call': {'outcome': 'failed', 'longrepr': 'strict mode violation locator(".a")'},
                         'teardown': {'outcome': 'failed', 'longrepr': 'AssertionError: cleanup incomplete'}}]}
    if exit_code != 1:
        del report['tests'][0]['teardown']
    report_path = tmp_path / 'report.json'
    report_path.write_text(json.dumps(report))
    state_path = tmp_path / 'pipeline.json'
    state_path.write_text(json.dumps({'step': 'reviewed', 'url': 'https://example.test',
                                     'execution_result': {'failed': 1, 'exit_code': exit_code,
                                                          'json_report_path': str(report_path)}}))
    monkeypatch.setattr(heal, 'PIPELINE_STATE', state_path)
    monkeypatch.setattr(sys, 'argv', ['06_heal.py'])
    import urllib.request
    monkeypatch.setattr(urllib.request, 'urlopen', lambda *a, **k: pytest.fail('must not probe or heal'))
    with pytest.raises(SystemExit) as stopped:
        heal.main()
    assert stopped.value.code == 2
    saved = json.loads(state_path.read_text())
    assert saved['step'] == 'heal_failed'
    assert saved['heal_context']['recovery']['can_heal'] is False
    if exit_code == 1:
        assert saved['heal_context']['recovery']['category'] == 'assertion'


def test_autoheal_blocks_abnormal_execution_even_with_locator_context(recovery, monkeypatch):
    heal, _, _, state = recovery
    saved = json.loads(state.read_text())
    saved['execution_result'] = {'status': 'failed', 'exit_code': 3, 'errors': [{'error': 'strict mode violation'}]}
    state.write_text(json.dumps(saved))
    monkeypatch.setattr(heal, '_refresh_heal_snapshot', lambda *a: pytest.fail('abnormal execution must not heal'))
    with pytest.raises(SystemExit) as stopped:
        heal.main()
    assert stopped.value.code == 5
