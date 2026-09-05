// ── Sidebar Update ──
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
    teamTabs.innerHTML = '<div style="padding:6px 14px;font-size:12px;color:var(--text-dim);">토론 없음</div>';
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
