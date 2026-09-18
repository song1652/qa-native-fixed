// Import Studio — 서버 API 호출 헬퍼
(function (NS) {
  'use strict';

  async function callApi(method, path, body) {
    const res = await fetch(path, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    let data;
    try {
      data = await res.json();
    } catch (_) {
      data = { error: `서버가 올바른 JSON을 반환하지 않았습니다. (HTTP ${res.status})` };
    }
    if (!res.ok || data?.ok === false) throw data;
    return data;
  }

  Object.assign(NS, { callApi });
})(window.__importStudioNS = window.__importStudioNS || {});
