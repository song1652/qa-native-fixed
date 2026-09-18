// Import Studio — 진입점: 메인 렌더 루프 + 초기화 + window.IS 공개 API
(function (NS) {
  'use strict';

  const { state } = NS;
  const { callApi } = NS;
  const { errorMessage } = NS;
  const {
    renderWizardHeader,
    renderStep1,
    renderStep2,
    renderStep3,
    renderStep4,
    renderStep5,
    renderModal,
  } = NS;

  function escHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ─────────────────────────────────────────
  // 메인 렌더 (async — Step1이 async fetch 포함)
  // ─────────────────────────────────────────
  // RAF 디바운스: 연속 render() 호출을 1프레임으로 합침
  let _renderRaf = null;
  let _renderPromise = null;
  async function render() {
    if (_renderPromise) return _renderPromise;
    _renderPromise = new Promise((resolve) => {
      _renderRaf = requestAnimationFrame(async () => {
        try {
          await _doRender();
        } finally {
          _renderRaf = null;
          _renderPromise = null;
          resolve();
        }
      });
    });
    return _renderPromise;
  }

  async function _doRender() {
    const container = document.getElementById('import-studio-root');
    if (!container) return;

    // 컨테이너에 .import-studio 클래스 적용 (단 한 번이면 충분하지만 idempotent)
    container.classList.add('import-studio');

    // Step 콘텐츠 생성 (Step1만 async)
    let stepInnerHtml = '';
    switch (state.step) {
      case 1: stepInnerHtml = await renderStep1(); break;
      case 2: stepInnerHtml = renderStep2();       break;
      case 3: stepInnerHtml = renderStep3();       break;
      case 4: stepInnerHtml = renderStep4();       break;
      case 5: stepInnerHtml = renderStep5();       break;
      default: stepInnerHtml = '';
    }

    // 에러 배너 (Step4는 내부에서 처리)
    const errorBanner = state.error && state.step !== 4
      ? `<div class="error-banner" role="alert">${escHtml(state.error)}</div>`
      : '';

    const liveStatus = state.error
      ? `오류: ${state.error}`
      : state.loading ? '처리 중입니다.'
      : `가져오기 ${state.step}단계`;

    container.innerHTML = `
      <div class="sr-only" role="status" aria-live="polite">${escHtml(liveStatus)}</div>
      <div class="page-header">
        <div class="page-title">Excel Import Studio</div>
        <div class="wizard">${renderWizardHeader()}</div>
        <button class="btn btn-ghost reset-btn" onclick="IS.startNewImport()" title="처음부터 다시 시작">↺ 리셋</button>
      </div>
      ${errorBanner}
      <div class="step-content active" aria-busy="${state.loading}">
        ${stepInnerHtml}
      </div>
      ${renderModal()}
    `;
  }

  // ─────────────────────────────────────────
  // 초기화
  // ─────────────────────────────────────────
  async function init(containerId) {
    const el = typeof containerId === 'string'
      ? (document.getElementById(containerId.replace(/^#/, '')) ||
         document.querySelector(containerId))
      : containerId;

    if (!el) {
      console.warn('[ImportStudio] container not found:', containerId);
      return;
    }

    el.id = 'import-studio-root';
    el.classList.add('import-studio'); // 아티팩트 스코프 클래스

    // 매핑 프로필 사전 로드
    try {
      const data = await callApi('GET', '/api/import/profiles');
      state.profiles = data.profiles || [];
    } catch (err) {
      state.profiles = [];
      state.error = errorMessage(err, '매핑 프로필을 불러오지 못했습니다. 서버 연결을 확인하세요.');
    }

    await render();
  }

  NS.render = render;

  // ─────────────────────────────────────────
  // Public API — onclick="IS.xxx()" 전역 접근용
  // ─────────────────────────────────────────
  const IS = {
    init,
    // 네비게이션
    next: NS.next,
    prev: NS.prev,
    goTo: NS.goTo,
    // Step1
    selectFile: NS.selectFile,
    toggleSheet: NS.toggleSheet,
    retryInit: NS.retryInit,
    // Step2
    setMapping: NS.setMapping,
    selectMappingSource: NS.selectMappingSource,
    setSourceMapping: NS.setSourceMapping,
    toggleConflictDecision: NS.toggleConflictDecision,
    saveProfile: NS.saveProfile,
    loadProfile: NS.loadProfile,
    deleteProfile: NS.deleteProfile,
    // Step3
    downloadCsv: NS.downloadCsv,
    setFilter: NS.setFilter,
    // Step4
    commit: NS.commit,
    selectPolicy: NS.selectPolicy,
    // Step5
    rollback: NS.rollback,
    startNewImport: NS.startNewImport,
    cancelModal: NS.cancelModal,
    submitModal: NS.submitModal,
    handleModalKeydown: NS.handleModalKeydown,
  };

  window.IS = IS;
})(window.__importStudioNS = window.__importStudioNS || {});
