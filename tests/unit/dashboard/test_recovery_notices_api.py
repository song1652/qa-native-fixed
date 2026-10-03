"""Recovery notices come from durable run history, including runs without reports."""
import json
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import pytest
import _paths

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json


@pytest.fixture(autouse=True)
def isolate_run_history(tmp_path, monkeypatch):
    monkeypatch.setattr(_paths, "RUN_HISTORY", tmp_path / "state" / "run_history.json")


def get_notices(base_url, endpoint="/api/recovery-notices"):
    try:
        with urlopen(base_url + endpoint) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, {}


def test_failed_run_without_report_survives_history_and_has_actionable_notice(tmp_path):
    state = tmp_path / 'state'
    state.mkdir()
    entry = {'run_id': 'run_failed', 'timestamp': '2026-10-03T10:00:00',
             'pipeline': 'single', 'groups': ['login'], 'status': 'failed',
             'total': 0, 'failed': 0, 'report_path': None,
             'recovery': {'category': 'browser_unavailable', 'title': '브라우저 확인 필요',
                          'message': 'Playwright 브라우저를 설치한 뒤 다시 실행하세요.',
                          'action': 'check_environment'}}
    (state / 'run_history.json').write_text(json.dumps([entry]))
    # The current pipeline belongs to a different run and cannot supply the cause.
    (state / 'pipeline.json').write_text(json.dumps({'execution_result': {
        'run_id': 'another_run', 'error': 'AssertionError: unrelated'}}))
    with dashboard_server(tmp_path) as base_url:
        status, body = get_notices(base_url)
        _, history = request_json(base_url, 'GET', '/api/run_history')
        _, repeated = get_notices(base_url)
    assert status == 200
    assert body['ok'] is True
    assert history == [entry]
    notice = body['notices'][0]
    assert notice['id'] == 'run:run_failed:failed'
    assert notice['category'] == 'browser_unavailable'
    assert notice['groups'] == ['login']
    assert notice['action_label'] and notice['href'] == '/?view=history'
    assert notice['message'] == entry['recovery']['message']
    assert repeated == body


def test_terminal_notices_are_recent_bounded_and_run_scoped(tmp_path):
    state = tmp_path / 'state'
    state.mkdir()
    entries = [{'run_id': f'run_{i}', 'status': 'failed', 'error': 'AssertionError',
                'timestamp': '2026-10-03T10:00:00', 'group': 'login'} for i in range(12)]
    entries += [{'run_id': 'passed', 'status': 'passed'},
                {'run_id': 'running', 'status': 'running'},
                {'run_id': 'timeout', 'status': 'timed_out'},
                {'run_id': 'stopped', 'status': 'interrupted'}]
    (state / 'run_history.json').write_text(json.dumps(entries))
    with dashboard_server(tmp_path) as base_url:
        status, body = get_notices(base_url, '/api/recovery_notices')
    assert status == 200
    notices = body['notices']
    assert len(notices) == 10
    assert [n['run_id'] for n in notices[:2]] == ['stopped', 'timeout']
    assert len({n['id'] for n in notices}) == 10
    assert notices[0]['category'] == 'interrupted'
    assert notices[1]['category'] == 'timeout'
    assert notices[2]['category'] == 'assertion'
    assert notices[2]['groups'] == ['login']


def test_legacy_failure_identity_is_stable_when_history_grows(tmp_path):
    state = tmp_path / 'state'
    state.mkdir()
    history = state / 'run_history.json'
    legacy = {'timestamp': '2026-10-02T09:00:00', 'pipeline': 'parallel',
              'groups': ['login'], 'failed': 1, 'total': 1}
    history.write_text(json.dumps([legacy]))
    with dashboard_server(tmp_path) as base_url:
        status, first = get_notices(base_url)
        assert status == 200
        history.write_text(json.dumps([legacy, {'run_id': 'new', 'status': 'failed'}]))
        _, second = get_notices(base_url)
    assert first['notices'][0]['id'] == second['notices'][1]['id']
    assert first['notices'][0]['run_id']


def test_empty_history_does_not_promote_stale_pipeline_failure(tmp_path):
    state = tmp_path / 'state'
    state.mkdir()
    (state / 'pipeline.json').write_text(json.dumps({'step': 'heal_failed',
        'execution_result': {'error': 'AssertionError', 'failed': 1}}))
    with dashboard_server(tmp_path) as base_url:
        status, body = get_notices(base_url)
    assert status == 200
    assert body == {'ok': True, 'notices': []}


def test_completed_healing_hides_older_failure_for_the_same_run(tmp_path):
    state = tmp_path / 'state'
    state.mkdir()
    (state / 'run_history.json').write_text(json.dumps([
        {'run_id': 'healed', 'status': 'failed', 'failed': 1},
        {'run_id': 'still_failed', 'status': 'failed', 'failed': 1},
        {'run_id': 'still_failed', 'status': 'failed', 'failed': 1},
        {'run_id': 'healed', 'status': 'passed', 'failed': 0},
    ]))
    with dashboard_server(tmp_path) as base_url:
        status, body = get_notices(base_url)
    assert status == 200
    assert [notice['run_id'] for notice in body['notices']] == ['still_failed']


def test_active_workflow_does_not_raise_notice_for_its_healing_attempt(tmp_path):
    state = tmp_path / 'state'
    state.mkdir()
    (state / 'run_history.json').write_text(json.dumps([
        {'run_id': 'active_healing', 'status': 'failed', 'failed': 1},
        {'run_id': 'older', 'status': 'failed', 'failed': 1},
    ]))
    (state / 'dashboard_execution.json').write_text(json.dumps({
        'run_id': 'active_healing', 'status': 'running'}))
    with dashboard_server(tmp_path) as base_url:
        status, body = get_notices(base_url)
    assert status == 200
    assert [notice['run_id'] for notice in body['notices']] == ['older']
