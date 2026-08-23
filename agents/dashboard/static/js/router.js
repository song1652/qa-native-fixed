// ── View Routing ──
function selectView(viewId) {
  currentView = viewId;
  document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('active'));
  const el = document.getElementById('tab-' + viewId);
  if (el) el.classList.add('active');
  renderCurrentView();
}

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
  } else if (currentView.startsWith('team_')) {
    renderTeamView(main);
  } else {
    renderDashboardOverview(main);
  }
}
