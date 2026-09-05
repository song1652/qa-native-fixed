// ── API & Data Fetching ──
async function fetchPipelineState() {
  try {
    const res = await fetch('/api/pipeline_state?' + Date.now());
    if (res.ok) pipelineState = await res.json();
  } catch (e) { }
}

async function fetchBatchState() {
  try {
    const res = await fetch('/api/batch_state?' + Date.now());
    if (res.ok) batchState = await res.json();
  } catch (e) { }
}

async function fetchReports() {
  try {
    const res = await fetch('/api/reports?' + Date.now());
    if (res.ok) reportsList = await res.json();
  } catch (e) { }
}

async function fetchPages() {
  try {
    const res = await fetch('/api/pages?' + Date.now());
    if (res.ok) pagesData = await res.json();
  } catch (e) { }
}

async function fetchGeneratedGroups() {
  try {
    const res = await fetch('/api/generated_groups?' + Date.now());
    if (res.ok) generatedGroups = await res.json();
  } catch (e) { }
}

async function fetchQuickState() {
  try {
    const res = await fetch('/api/quick_state?' + Date.now());
    if (res.ok) quickState = await res.json();
  } catch (e) { }
}

function _shouldSkipRender() {
  // 사용자가 select/input 조작 중이면 스킵
  const mainEl = document.getElementById('main');
  if (mainEl && mainEl.contains(document.activeElement)
    && (document.activeElement.tagName === 'SELECT' || document.activeElement.tagName === 'INPUT')) {
    return true;
  }
  // iframe이 열려 있으면 스킵 (리포트 보는 중)
  const reportWrap = document.getElementById('report-iframe-wrap');
  if (reportWrap && reportWrap.style.display !== 'none') return true;
  const parallelReportWrap = document.getElementById('parallel-report-wrap');
  if (parallelReportWrap && parallelReportWrap.style.display !== 'none') return true;
  const singleReportWrap = document.getElementById('single-report-wrap');
  if (singleReportWrap && singleReportWrap.style.display !== 'none') return true;
  // 빠른 실행 중 로그 폴링 시 DOM 재생성 방지
  if (currentView === 'quick_run' && _quickRunState.running) return true;
  // Import Studio는 자체 상태 관리 — 5초 폴링 시 전체 재렌더 방지
  if (currentView === 'import_studio') return true;
  return false;
}

function _saveScrollPos() {
  const scroll = document.querySelector('.content-scroll');
  if (scroll && currentView) _uiState.scrollTop[currentView] = scroll.scrollTop;
}

function _restoreScrollPos() {
  const scroll = document.querySelector('.content-scroll');
  if (scroll && currentView && _uiState.scrollTop[currentView]) {
    scroll.scrollTop = _uiState.scrollTop[currentView];
  }
}

var _confirmOpen = false;

async function refreshAll() {
  // confirm/prompt 팝업이 열려있으면 리렌더 스킵 (팝업 강제 닫힘 방지)
  if (_confirmOpen) return;

  await Promise.all([
    fetch('/api/dialogs?' + Date.now()).then(r => r.ok ? r.text() : null).then(t => { if (t) applyDialogData(t); }),
    fetchPipelineState(),
    fetchBatchState(),
    fetchReports(),
    fetchPages(),
    fetchGeneratedGroups(),
    fetchQuickState(),
  ]);
  updateSidebar(lastData || {});
  if (!_shouldSkipRender()) {
    _saveScrollPos();
    renderCurrentView();
    _restoreScrollPos();
  }
}

// confirm 래퍼 — 커스텀 모달 (SSE로 네이티브 confirm 닫힘 방지)
function safeConfirm(msg) {
  return new Promise(resolve => {
    _confirmOpen = true;
    const overlay = document.createElement('div');
    overlay.id = 'confirm-modal';
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:99999;';
    const box = document.createElement('div');
    box.style.cssText = 'background:rgba(18,16,42,0.95);backdrop-filter:blur(20px);border:1px solid rgba(140,120,220,0.2);border-radius:12px;padding:28px 32px;max-width:400px;text-align:center;box-shadow:0 16px 48px rgba(0,0,0,0.5);';
    box.innerHTML = `
      <p style="color:var(--text);font-size:14px;margin:0 0 24px;line-height:1.6;">${msg}</p>
      <div style="display:flex;gap:10px;justify-content:center;">
        <button id="confirm-yes" style="background:var(--accent);color:#fff;border:none;border-radius:8px;padding:9px 24px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;">확인</button>
        <button id="confirm-no" style="background:transparent;color:var(--text-dim);border:1px solid var(--border);border-radius:8px;padding:9px 24px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;">취소</button>
      </div>`;
    overlay.appendChild(box);
    document.body.appendChild(overlay);
    const close = (val) => { _confirmOpen = false; overlay.remove(); document.removeEventListener('keydown', handleKey); resolve(val); };
    const handleKey = (e) => { if (e.key === 'Escape') close(false); };
    document.addEventListener('keydown', handleKey);
    document.getElementById('confirm-yes').onclick = () => close(true);
    document.getElementById('confirm-no').onclick = () => close(false);
    overlay.addEventListener('click', e => { if (e.target === overlay) close(false); });
  });
}

// SSE — state/pipeline.json 변경 시 파이프라인 상태도 즉시 갱신
function connectSSE() {
  const es = new EventSource('/api/events');
  es.onmessage = async e => {
    if (_confirmOpen) return;
    applyDialogData(e.data);
    await fetchPipelineState();
    await fetchBatchState();
    if (!_shouldSkipRender()) {
      _saveScrollPos();
      renderCurrentView();
      _restoreScrollPos();
    }
  };
  es.onerror = () => { es.close(); setTimeout(connectSSE, 5000); };
}

function applyDialogData(text) {
  if (text === lastJson) return;
  lastJson = text;
  lastData = JSON.parse(text);
  refreshCount++;
  const now = new Intl.DateTimeFormat(navigator.language || 'ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(new Date());
  document.getElementById('header-meta').textContent = `${now} · ${refreshCount}회`;
  updateSidebar(lastData);
  if (currentView.startsWith('team_') || currentView === '') renderCurrentView();
}
