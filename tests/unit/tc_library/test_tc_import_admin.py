from __future__ import annotations

import json
import http.client
from urllib.parse import urlsplit

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json

BASE = '/api/tc-library/import'
MAPPING = {'header_row': 3, 'columns': {
    'feature': 'B', 'steps': 'C', 'expected': 'D', 'source_tc_id': 'A',
    'tags': 'E', 'l2': 'G', 'l3': 'H'}}


def test_mapping_profile_crud_preserves_legacy_storage(tmp_path):
    project = tmp_path / 'project'
    with dashboard_server(project) as url:
        status, body = request_json(url, 'POST', BASE + '/mapping-profiles', {'name': 'custom', 'mapping': MAPPING})
        assert status == 201, body
        profile = body['profile']
        assert profile['mapping'] == MAPPING
        stored = json.loads((project / 'state/import_profiles.json').read_text())['profiles'][0]
        assert stored['mappings']['tc_id'] == 'A열'
        assert stored['mappings']['title'] == 'B열'
        assert request_json(url, 'GET', BASE + '/mapping-profiles')[1]['profiles'][0]['columns'] == MAPPING['columns']
        assert request_json(url, 'GET', '/api/import/profiles')[1]['profiles'][0]['id'] == profile['id']
        target = BASE + '/mapping-profiles/' + profile['id']
        assert request_json(url, 'PUT', target, {'name': 'renamed', 'mapping': MAPPING})[1]['profile']['name'] == 'renamed'
        assert request_json(url, 'POST', BASE + '/mapping-profiles', {'name': 'renamed', 'mapping': MAPPING})[0] == 409
        assert request_json(url, 'DELETE', target)[1]['deleted'] == profile['id']
        assert request_json(url, 'GET', BASE + '/mapping-profiles')[1]['profiles'] == []


def test_mapping_profile_validation_and_legacy_read(tmp_path):
    project = tmp_path / 'project'
    with dashboard_server(project) as url:
        request_json(url, 'POST', '/api/import/profiles', {'name': 'old', 'mappings': {'title': 'B열', 'steps': 'C열', 'expected': 'D열', 'tc_id': 'A열', 'tags': 'E열'}})
        profile = request_json(url, 'GET', BASE + '/mapping-profiles')[1]['profiles'][0]
        assert profile['mapping']['header_row'] == 1
        assert profile['mapping']['columns']['source_tc_id'] == 'A'
        for mapping in ({'columns': {'feature': 'B'}}, {**MAPPING, 'header_row': 0}, {**MAPPING, 'columns': {**MAPPING['columns'], 'steps': 'XFE'}}):
            assert request_json(url, 'POST', BASE + '/mapping-profiles', {'name': 'bad', 'mapping': mapping})[0] == 400


def test_md_history_skips_corrupt_journal_and_sanitizes_details(tmp_path):
    project = tmp_path / 'project'
    with dashboard_server(project) as url:
        sessions = project / 'state/import_sessions'
        sessions.mkdir(parents=True, exist_ok=True)
        run = {'run_id': 'run_old', 'status': 'preview_ready', 'created_at': '2026-09-30', 'summary': {'new': 1}, 'sources': [], 'rows': [{'tc_id': 'A', '_target': '/private/internal', '_source_file': 'a.xlsx'}], 'internal_path': '/private/secret'}
        (sessions / 'run_old.json').write_text(json.dumps(run))
        (sessions / 'run_broken.json').write_text('{')
        status, body = request_json(url, 'GET', BASE + '/md-runs')
        assert status == 200
        assert [r['run_id'] for r in body['runs']] == ['run_old']
        assert body['errors'][0]['run_id'] == 'run_broken'
        details = request_json(url, 'GET', BASE + '/md-runs/run_old')[1]
        assert '_target' not in details['rows'][0]
        assert 'internal_path' not in details
        assert details['skipped_csv_url'] == '/api/import/runs/run_old/skipped.csv'


def test_md_history_rollback_routes_library_and_legacy_runs(tmp_path, monkeypatch):
    import _tc_md_export
    import _import_commit
    calls = []
    monkeypatch.setattr(_tc_md_export, 'rollback', lambda suite, run_id: calls.append(('library', suite, run_id)) or {'status': 'rolled_back'})
    monkeypatch.setattr(_import_commit, 'rollback_run', lambda run_id, *args: calls.append(('legacy', run_id)) or {'status': 'rolled_back'})
    with dashboard_server(tmp_path / 'project') as url:
        import _paths
        _paths.IMPORT_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        for rid, extra in [('run_library', {'tc_library_suite': 'suite'}), ('run_legacy', {})]:
            (_paths.IMPORT_SESSIONS_DIR / (rid + '.json')).write_text(json.dumps({'run_id': rid, 'status': 'committed', **extra}))
            assert request_json(url, 'POST', BASE + '/md-runs/' + rid + '/rollback', {})[0] == 200
    assert calls == [('library', 'suite', 'run_library'), ('legacy', 'run_legacy')]


def test_invalid_mapping_and_malformed_json_return_validation_errors(tmp_path):
    with dashboard_server(tmp_path / 'project') as url:
        status, created = request_json(url, 'POST', BASE + '/mapping-profiles', {'name': 'valid', 'mapping': MAPPING})
        assert status == 201
        target = BASE + '/mapping-profiles/' + created['profile']['id']
        for method, path in [('POST', BASE + '/mapping-profiles'), ('PUT', target)]:
            for value in ({}, [], None):
                status, body = request_json(url, method, path, {'name': 'invalid', 'mapping': {**MAPPING, 'columns': value}})
                assert (status, body['code']) == (400, 'INVALID_PROFILE')
            connection = http.client.HTTPConnection(urlsplit(url).netloc)
            connection.request(method, path, body=b'{', headers={'Content-Type': 'application/json'})
            response = connection.getresponse()
            assert response.status == 400
            assert json.loads(response.read())['code'] == 'INVALID_JSON'
            connection.request('GET', BASE + '/mapping-profiles')
            response = connection.getresponse()
            assert response.status == 200
            assert json.loads(response.read())['profiles'][0]['name'] == 'valid'
            connection.close()


def test_delete_rejects_oversized_body_without_deleting_profile(tmp_path):
    from dash_http import MAX_JSON_BODY_BYTES
    with dashboard_server(tmp_path / 'project') as url:
        created = request_json(url, 'POST', BASE + '/mapping-profiles', {'name': 'valid', 'mapping': MAPPING})[1]
        target = BASE + '/mapping-profiles/' + created['profile']['id']
        connection = http.client.HTTPConnection(urlsplit(url).netloc)
        connection.request('DELETE', target, body=b'', headers={'Content-Length': str(MAX_JSON_BODY_BYTES + 1)})
        response = connection.getresponse()
        assert response.status == 413
        assert json.loads(response.read())['code'] == 'PAYLOAD_TOO_LARGE'
        connection.close()
        assert len(request_json(url, 'GET', BASE + '/mapping-profiles')[1]['profiles']) == 1
