// ── View Routing ──
const TC_STUDIO_PATH = '/tc-studio';

function _viewToPath(viewId) {
  if (viewId === 'import_studio') return TC_STUDIO_PATH;
  if (viewId === 'tc_studio') return TC_STUDIO_PATH;
  if (!viewId) return '/';
  return '/?view=' + encodeURIComponent(viewId);
}

function _pathToView() {
  if (window.location.pathname === TC_STUDIO_PATH) return 'tc_studio';
  const params = new URLSearchParams(window.location.search);
  return params.get('view') === 'import_studio' ? 'tc_studio' : params.get('view') || '';
}

if (new URLSearchParams(window.location.search).get('view') === 'import_studio') {
  window.history.replaceState({ viewId: 'tc_studio' }, '', TC_STUDIO_PATH);
}

// 초기 뷰를 URL에서 복원
currentView = _pathToView();

function selectView(viewId, options = {}) {
  viewId = viewId === 'import_studio' ? 'tc_studio' : viewId;
  currentView = viewId;
  const nextPath = _viewToPath(viewId);
  const currentPath = window.location.pathname + window.location.search;
  if (!options.fromHistory && currentPath !== nextPath) {
    window.history.pushState({ viewId }, '', nextPath);
  }
  document.querySelectorAll('.sidebar-item').forEach(el => { el.classList.remove('active'); el.removeAttribute('aria-current'); });
  const el = document.getElementById('tab-' + viewId);
  if (el) { el.classList.add('active'); el.setAttribute('aria-current', 'page'); }
  renderCurrentView();
}

window.addEventListener('popstate', () => {
  selectView(_pathToView(), { fromHistory: true });
});

function renderCurrentView() {
  if (_confirmOpen) return;
  renderHeaderStatus();
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
  } else if (currentView === 'tc_studio') {
    main.innerHTML = '<div id="tc-studio-root"></div>';
    if (window.TCS) {
      window.TCS.init('#tc-studio-root').catch(console.error);
    } else {
      main.innerHTML = '<div style="padding:40px;color:var(--text-dim);">TC 스튜디오 로딩 실패 — 페이지를 새로고침하세요.</div>';
    }
  } else if (currentView === 'team_new') {
    renderTeamNew(main);
  } else if (currentView.startsWith('team_')) {
    renderTeamView(main);
  } else {
    renderDashboardOverview(main);
  }
}

if (currentView) {
  queueMicrotask(() => selectView(currentView, { fromHistory: true }));
}
