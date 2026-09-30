// TC 스튜디오 — API 클라이언트 (agents/dashboard/routes_tc_library.py와 1:1)
(function (NS) {
  'use strict';

  const enc = encodeURIComponent;

  async function request(method, path, body) {
    const init = { method, headers: {} };
    if (body instanceof Blob) {
      init.body = body;
      init.headers['Content-Type'] = 'application/octet-stream';
    } else if (body !== undefined) {
      init.body = JSON.stringify(body);
      init.headers['Content-Type'] = 'application/json';
    }
    const res = await fetch(path, init);
    const data = await res.json().catch(() => ({ ok: false, code: 'BAD_RESPONSE' }));
    if (!res.ok) {
      const err = new Error(data.error || res.statusText);
      err.status = res.status;
      err.code = data.code;
      err.data = data;
      throw err;
    }
    return data;
  }

  const S = (suite) => `/api/tc-library/${enc(suite)}`;
  const C = (suite, id) => `${S(suite)}/cases/${enc(id)}`;

  NS.api = {
    suites: () => request('GET', '/api/tc-library'),
    tree: (suite) => request('GET', `${S(suite)}/tree`),
    list: (suite, query) => request('GET', `${S(suite)}?${new URLSearchParams(query)}`),
    getCase: (suite, id) => request('GET', C(suite, id)),
    patchCase: (suite, id, rev, changes) => request('PATCH', C(suite, id), { rev, ...changes }),
    createCase: (suite, fields) => request('POST', `${S(suite)}/cases`, fields),
    duplicate: (suite, id) => request('POST', `${C(suite, id)}/duplicate`),
    deleteCase: (suite, id, rev) => request('DELETE', `${C(suite, id)}?rev=${rev}`),
    restore: (suite, id) => request('POST', `${C(suite, id)}/restore`),
    history: (suite, id) => request('GET', `${C(suite, id)}/history`),
    revert: (suite, id, historyId, rev) =>
      request('POST', `${C(suite, id)}/revert`, { history_id: historyId, rev }),
    bulk: (suite, items, op, field, value) =>
      request('POST', `${S(suite)}/bulk`, { items, op, field, value }),
    move: (suite, items, sheet, path, feature) =>
      request('POST', `${S(suite)}/move`, { items, sheet, path, feature }),
    importPreview: (file) =>
      request('POST', `/api/tc-library/import/preview?filename=${enc(file.name)}`, file),
    importCommit: (payload) => request('POST', '/api/tc-library/import', payload),
    exportXlsx: (suite, payload) => request('POST', `${S(suite)}/export/xlsx`, payload),
    downloadUrl: (exportId) => `/api/tc-library/exports/${enc(exportId)}/download`,
  };
})(window.TCS_NS = window.TCS_NS || {});
