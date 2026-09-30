// TC 스튜디오 — 화면 상태와 공용 도우미
(function (NS) {
  'use strict';

  NS.state = {
    suites: [],
    suite: '',
    tree: [],
    items: [],          // 현재 필터 결과 (서버 응답 그대로, issues 포함)
    total: 0,
    filters: { q: '', path: '', status: '', execution_result: '', priority: '', auto: '',
               source: '', invalid: false, needs_review: false },
    selected: new Set(),
    activeId: '',
    screen: 'library',
    lastUndo: null,     // { label, run: async () => {} }
  };

  NS.STATUS_LABEL = { draft: '초안', approved: '승인', rejected: '반려', needs_review: '재검토 필요' };
  NS.RESULT_LABEL = { '': '미실행', pass: 'Pass', fail: 'Fail', not_test: 'Not Test', na: 'N/A' };
  NS.PRIORITIES = ['P0', 'P1', 'P2', 'P3'];
  NS.AUTO_VALUES = ['Y-web', 'Y-app', 'N'];

  // 필터 → GET /api/tc-library/{suite} 쿼리. 실행 결과 "none" = 미실행(빈 값).
  NS.queryFromFilters = function (f) {
    const q = {};
    Object.entries(f).forEach(([k, v]) => {
      if (k === 'invalid' || k === 'needs_review') { if (v) q[k] = '1'; return; }
      if (k === 'execution_result') {
        if (v === 'none') q.execution_result = '';
        else if (v) q.execution_result = v;
        return;
      }
      if (v) q[k] = v;
    });
    return q;
  };

  NS.esc = function (s) {
    return String(s ?? '').replace(/[&<>"]/g, (c) => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  };

  NS.$ = (sel, root = document) => root.querySelector(sel);
  NS.$$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  // 목업 toast() 이식. actions: [{ id, label, fn }]
  NS.toast = function (msg, kind = '', actions = [], ms = 3800) {
    const box = NS.$('#tcs-toasts');
    if (!box) return null;
    const el = document.createElement('div');
    el.className = 'toast ' + kind;
    el.innerHTML = `<div>${msg}</div>` + (actions.length
      ? `<div class="row">${actions.map((a, i) =>
        `<button class="btn-sm" data-id="${a.id}" data-i="${i}">${NS.esc(a.label)}</button>`).join('')}</div>`
      : '');
    actions.forEach((a, i) => el.querySelector(`[data-i="${i}"]`).addEventListener('click', async () => {
      el.remove();
      if (a.fn) await a.fn();
    }));
    box.appendChild(el);
    if (ms) setTimeout(() => el.remove(), ms);
    return el;
  };
})(window.TCS_NS = window.TCS_NS || {});
