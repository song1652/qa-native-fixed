// TC 스튜디오 — 진입점: 셸 렌더, 스위트 선택, 화면 전환. 공개 API: window.TCS.init(selector)
(function (NS) {
  'use strict';

  const { state, api, esc, $, $$ } = NS;
  const SUITE_KEY = 'tcs-suite';
  let root = null;

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
    <nav class="wizard" role="tablist" aria-label="스튜디오 화면">
      <button class="step-item" role="tab" data-id="nav-tab-library" data-screen="library" aria-selected="true"><span class="step-circle">1</span><span class="step-label">TC 라이브러리</span><span class="step-count num" id="cnt-lib">0</span></button>
      ${NS.exportView ? '<div class="step-line"></div><button class="step-item" role="tab" data-id="nav-tab-export" data-screen="export" aria-selected="false"><span class="step-circle">2</span><span class="step-label">내보내기</span></button>' : ''}
    </nav>
  </header>
  ${NS.library.html()}
  ${NS.exportView ? NS.exportView.html() : ''}
 </div>
 ${NS.importModal ? NS.importModal.html() : ''}
 <div class="toasts" id="tcs-toasts" aria-live="polite"></div>
</div>`;
  }

  function show(screen) {
    state.screen = screen;
    $$('.step-item', root).forEach((b) => b.setAttribute('aria-selected', b.dataset.screen === screen));
    $$('.screen', root).forEach((s) => s.classList.toggle('active', s.dataset.screen === screen));
    if (screen === 'export' && NS.exportView) NS.exportView.onShow();
  }

  function renderSuiteSelect() {
    const sel = $('#suite-select', root);
    sel.innerHTML = state.suites.map((s) => `<option value="${esc(s.suite)}" ${s.suite === state.suite ? 'selected' : ''}>${esc(s.suite)} (${s.count})</option>`).join('')
      || '<option value="">스위트 없음</option>';
    sel.disabled = !state.suites.length;
    const cur = state.suites.find((s) => s.suite === state.suite);
    $('#cnt-lib', root).textContent = cur ? cur.count : 0;
  }

  // 가져오기 후에도 호출된다 (import.js)
  NS.reloadSuites = async function (prefer) {
    state.suites = (await api.suites()).suites;
    let saved = prefer || '';
    if (!saved) { try { saved = localStorage.getItem(SUITE_KEY) || ''; } catch (e) { saved = ''; } }
    state.suite = state.suites.some((s) => s.suite === saved) ? saved : (state.suites[0] ? state.suites[0].suite : '');
    try { if (state.suite) localStorage.setItem(SUITE_KEY, state.suite); } catch (e) { /* 저장 불가 환경 */ }
    renderSuiteSelect();
    state.selected.clear();
    await NS.library.refresh();
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
    NS.library.mount(root);
    // 가져오기(W2)·내보내기(W3) 모듈은 스크립트가 로드된 경우에만 붙는다
    if (NS.importModal) NS.importModal.mount(root);
    if (NS.exportView) NS.exportView.mount(root);
    $$('.step-item', root).forEach((b) => b.addEventListener('click', () => show(b.dataset.screen)));
    if (NS.importModal) $('#btn-import-xlsx', root).addEventListener('click', () => NS.importModal.open());
    $('#suite-select', root).addEventListener('change', (e) => NS.reloadSuites(e.target.value));
    show('library');
    await NS.reloadSuites();
  }

  window.TCS = { init };
})(window.TCS_NS = window.TCS_NS || {});
