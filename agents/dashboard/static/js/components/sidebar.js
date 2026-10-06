// ── Sidebar Update ──
function renderHeaderStatus() {
  const single = pipelineState || {};
  const parallel = (batchState || {}).parallel_state || {};
  const singleLabel = single.step ? (STEP_LABELS[single.step] || single.step) : '대기';
  const parallelLabel = parallel.status ? (PARALLEL_STEP_LABELS[parallel.status] || parallel.status) : '대기';
  const latest = [single.execution_result?.executed_at, parallel.execution_result?.executed_at,
    quickState?.execution_result?.executed_at, (_ovRunHistory || []).at(-1)?.timestamp].filter(Boolean).sort().at(-1);
  const count = parallel.execution_result?.total ? ` ${parallel.execution_result.passed || 0}/${parallel.execution_result.total}` : '';
  document.getElementById('header-meta').innerHTML = `<span class="header-server">대시보드 서버 · <code>${esc(location.host)}</code></span><span>단일 파이프라인 · ${esc(singleLabel)}</span><span>병렬 파이프라인 · ${esc(parallelLabel)}${count}</span>${latest ? `<span>마지막 실행 · <code>${esc(latest.slice(5, 16))}</code></span>` : ''}`;
}

function updateSidebar(data) {
  const teamTabs = document.getElementById('team-tabs');
  const teamSessions = data.team_sessions || [];
  if (teamSessions.length > 0) {
    teamTabs.innerHTML = teamSessions.map((s, idx) => {
      const tid = 'team_' + idx;
      const dotCls = s.completed_at ? 'pending' : s.status === 'discussed' ? 'waiting-vote' : s.status === 'in_progress' ? 'active-run' : 'pending';
      const isActive = currentView === tid;
      const label = s.topic || s.stage_label || '토론';
      return `<button type="button" class="sidebar-item${isActive ? ' active' : ''}" id="tab-${tid}" onclick="selectView('${tid}')"><div class="sidebar-dot ${dotCls}"></div><span class="sidebar-name" title="${esc(label)}">${esc(label)}</span></button>`;
    }).join('');
  } else {
    teamTabs.innerHTML = '<div style="padding:6px 24px;font-size:12px;color:var(--text-dim);">토론 없음</div>';
  }

  // 파이프라인 dot 업데이트
  const singleDot = document.getElementById('dot-single');
  if (singleDot && pipelineState && pipelineState.step) {
    const s = pipelineState.step;
    singleDot.className = 'sidebar-dot ' + (s === 'done' ? 'done' : (s !== 'init' ? 'active-run' : ''));
  }
  const parallelDot = document.getElementById('dot-parallel');
  if (parallelDot && batchState) {
    const pStatus = (batchState.parallel_state || {}).status || '';
    let dotCls = '';
    if (pStatus === 'done') dotCls = 'done';
    else if (['analyzing', 'ready', 'generating', 'testing', 'heal_needed'].includes(pStatus)) dotCls = 'active-run';
    else if (pStatus === 'heal_failed') dotCls = 'pending';
    parallelDot.className = 'sidebar-dot ' + dotCls;
  }

  const quickDot = document.getElementById('dot-quick');
  if (quickDot && quickState) {
    const qStep = quickState.step || '';
    let dotCls = '';
    if (qStep === 'done') dotCls = 'done';
    else if (qStep && qStep !== 'init') dotCls = 'active-run';
    quickDot.className = 'sidebar-dot ' + dotCls;
  }
}
