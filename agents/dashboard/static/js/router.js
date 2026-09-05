// ── View Routing ──
const IMPORT_STUDIO_PATH = '/import-studio';

function _viewToPath(viewId) {
  if (viewId === 'import_studio') return IMPORT_STUDIO_PATH;
  if (!viewId) return '/';
  return '/?view=' + encodeURIComponent(viewId);
}

function _pathToView() {
  if (window.location.pathname === IMPORT_STUDIO_PATH) return 'import_studio';
  const params = new URLSearchParams(window.location.search);
  return params.get('view') || '';
}

// 초기 뷰를 URL에서 복원
currentView = _pathToView();

function selectView(viewId, options = {}) {
  currentView = viewId;
  const nextPath = _viewToPath(viewId);
  const currentPath = window.location.pathname + window.location.search;
  if (!options.fromHistory && currentPath !== nextPath) {
    window.history.pushState({ viewId }, '', nextPath);
  }
  document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
  const el = document.getElementById('tab-' + viewId);
  if (el) el.classList.add('active');
  renderCurrentView();
}

window.addEventListener('popstate', () => {
  selectView(_pathToView(), { fromHistory: true });
});

function renderCurrentView() {
  if (_confirmOpen) return;
  const main = document.getElementById('main');
  if (currentView === 'single_pipeline') {
    renderSinglePipeline(main);
  } else if (currentView === 'parallel_pipeline') {
    renderParallelPipeline(main);
  } else if (currentView === 'quick_run') {
    renderQuickRun(main);
  } else if (currentView === 'reports') {
    renderReports(main);
  } else if (currentView === 'history') {
    renderHistory(main);
  } else if (currentView === 'pages') {
    renderPages(main);
  } else if (currentView === 'import_studio') {
    main.innerHTML = '<div id="import-studio-root" style="padding:0;"></div>';
    if (window.IS) {
      window.IS.init('#import-studio-root').catch(console.error);
    } else {
      main.innerHTML = '<div style="padding:40px;color:var(--text-dim);">Import Studio 로딩 실패 — 페이지를 새로고침하세요.</div>';
    }
  } else if (currentView.startsWith('team_')) {
    renderTeamView(main);
  } else {
    renderDashboardOverview(main);
  }
}

if (currentView) {
  queueMicrotask(() => selectView(currentView, { fromHistory: true }));
}
