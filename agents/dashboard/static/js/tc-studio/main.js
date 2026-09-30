// TC 스튜디오 — 진입점: 셸 렌더, 스위트 선택, 화면 전환. 공개 API: window.TCS.init(selector)
// 화면 모듈(generateView·reviewView·exportView·importModal)은 스크립트가 로드된 것만 붙는다.
(function (NS) {
  'use strict';

  const { state, api, esc, $, $$ } = NS;
  const SUITE_KEY = 'tcs-suite';
  const SCREENS = [
    { id: 'generate', label: '기획 정보 · TC 생성', module: 'generateView' },
    { id: 'library', label: 'TC 라이브러리', module: 'library', count: 'cnt-lib' },
    { id: 'review', label: '초안 검토', module: 'reviewView', count: 'cnt-review' },
    { id: 'export', label: '내보내기', module: 'exportView' },
  ];
  let root = null;
  let screenVersion = 0;

  const available = () => SCREENS.filter((s) => NS[s.module]);

  function navHtml() {
    return available().map((s, i) => `${i ? '<div class="step-line"></div>' : ''}<button class="step-item" role="tab" data-id="nav-tab-${s.id}" data-screen="${s.id}" aria-selected="${i === 0}"><span class="step-circle">${i + 1}</span><span class="step-label">${s.label}</span>${s.count ? `<span class="step-count num" id="${s.count}">0</span>` : ''}</button>`).join('');
  }

  function shellHtml() {
    return `
<div class="tc-studio">
 <div class="studio" id="studio">
  <header class="page-header">
    <div class="ph-top">
      <div><div class="crumb">QA CONTROL CENTER › 테스트케이스</div><h1 class="page-title">TC 스튜디오</h1></div>
      <select class="suite-select" id="suite-select" data-id="suite-select" aria-label="스위트 선택"></select>
      <span class="spacer"></span>
      ${NS.importModal ? '<button class="btn btn-ghost" data-id="btn-import-xlsx" id="btn-import-xlsx">엑셀 가져오기</button>' : ''}
    </div>
    <nav class="wizard" role="tablist" aria-label="스튜디오 화면">${navHtml()}</nav>
  </header>
  ${available().map((s) => NS[s.module].html()).join('')}
 </div>
 ${NS.importModal ? NS.importModal.html() : ''}
 <div class="toasts" id="tcs-toasts" aria-live="polite"></div>
</div>`;
  }

  function show(screen) {
    screenVersion++;
    state.screen = screen;
    $$('.step-item', root).forEach((b) => b.setAttribute('aria-selected', b.dataset.screen === screen));
    $$('.screen', root).forEach((s) => s.classList.toggle('active', s.dataset.screen === screen));
    const spec = SCREENS.find((s) => s.id === screen);
    if (spec && NS[spec.module].onShow) NS[spec.module].onShow();
  }
  NS.show = show;

  function renderSuiteSelect() {
    const sel = $('#suite-select', root);
    sel.innerHTML = state.suites.map((s) => `<option value="${esc(s.suite)}" ${s.suite === state.suite ? 'selected' : ''}>${esc(s.suite)} (${s.count})</option>`).join('')
      || '<option value="">스위트 없음</option>';
    sel.disabled = !state.suites.length;
    const cur = state.suites.find((s) => s.suite === state.suite);
    $('#cnt-lib', root).textContent = cur ? cur.count : 0;
  }

  // 케이스 추가·삭제·복제 뒤 스위트 선택 상자의 "(건수)"를 맞춘다 (선택한 스위트는 바꾸지 않는다)
  NS.refreshSuiteCounts = async function () {
    const { suites } = await api.suites();
    state.suites = suites;
    renderSuiteSelect();
  };

  NS.refreshCounts = async function () {
    const badge = $('#cnt-review', root);
    if (!badge || !state.suite) return;
    badge.textContent = (await api.list(state.suite, { status: 'draft', limit: 1 })).total;
  };

  // 가져오기 후에도 호출된다 (import.js)
  NS.reloadSuites = async function (prefer) {
    const previousSuite = state.suite;
    const navigationVersion = screenVersion;
    state.suites = (await api.suites()).suites;
    let saved = prefer || '';
    if (!saved) { try { saved = localStorage.getItem(SUITE_KEY) || ''; } catch (e) { saved = ''; } }
    state.suite = state.suites.some((s) => s.suite === saved) ? saved : (state.suites[0] ? state.suites[0].suite : '');
    try { if (state.suite) localStorage.setItem(SUITE_KEY, state.suite); } catch (e) { /* 저장 불가 환경 */ }
    renderSuiteSelect();
    state.selected.clear();
    const changed = previousSuite !== state.suite;
    if (changed) {
      Object.keys(state.filters).forEach((k) => { state.filters[k] = ['invalid', 'needs_review'].includes(k) ? false : ''; });
      $$('.filterbar select, .filterbar input, #tree-search', root).forEach((el) => { el.value = ''; });
      $$('.filterbar .fchip', root).forEach((el) => el.setAttribute('aria-pressed', 'false'));
      NS.detail.close({ force: true });
      state.reviewJob = null;
    }
    await NS.library.refresh();
    await NS.refreshCounts();
    if (changed && NS.generateView) {
      const suite = state.suite;
      const context = suite ? await api.authoringContext(suite) : { job: null };
      if (state.suite !== suite) return;
      await NS.generateView.loadSuite(context.job, screenVersion !== navigationVersion);
      if (state.suite !== suite) return;
      const current = state.suites.find((s) => s.suite === suite);
      if (screenVersion === navigationVersion) show(current && current.count ? 'library' : 'generate');
    }
  };

  // 화면 이벤트에서 시작한 요청이 실패하면(서버 재시작·네트워크 끊김) 처리되지 않은 오류로 남기지 않고
  // 토스트로 알린다. 스튜디오가 화면에 있을 때만 가로챈다 (다른 대시보드 화면의 오류는 건드리지 않는다).
  window.addEventListener('unhandledrejection', (e) => {
    if (!root || !document.body.contains(root)) return;
    e.preventDefault();
    NS.toast(`요청을 처리하지 못했습니다: ${esc((e.reason && e.reason.message) || e.reason)}`, 'err');
  });

  async function init(selector) {
    root = document.querySelector(selector);
    root.innerHTML = shellHtml();
    available().forEach((s) => NS[s.module].mount(root));
    if (NS.importModal) NS.importModal.mount(root);
    $$('.step-item', root).forEach((b) => b.addEventListener('click', () => show(b.dataset.screen)));
    if (NS.importModal) $('#btn-import-xlsx', root).addEventListener('click', () => NS.importModal.open());
    $('#suite-select', root).addEventListener('change', async (e) => {
      const next = e.target.value;
      if (!(await NS.detail.confirmLeave())) { e.target.value = state.suite; return; }
      await NS.reloadSuites(next);
    });
    show('library');
    await NS.reloadSuites();
  }

  window.TCS = { init };
})(window.TCS_NS = window.TCS_NS || {});
