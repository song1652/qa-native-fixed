// ── Dashboard Overview (OAXIS-inspired) ──

async function resetDashboard() {
  if (!(await safeConfirm('대시보드를 초기화하시겠습니까?\n(힐링 통계, 실행 이력)'))) return;
  await Promise.all([
    fetch('/api/heal_stats/reset', { method: 'POST' }),
    fetch('/api/run_history/reset', { method: 'POST' }),
  ]);
  const main = document.getElementById('main');
  if (main) renderDashboardOverview(main);
}

async function _loadOverviewData() {
  try {
    const [rh, hs, flaky] = await Promise.all([
      fetch('/api/run_history').then(r => r.json()),
      fetch('/api/heal_stats').then(r => r.json()),
      fetch('/api/flaky_tests').then(r => r.json()).catch(() => null),
    ]);
    _ovRunHistory = rh || [];
    _ovHealStats = hs || {};
    _ovFlakyTests = flaky || null;
  } catch(e) { _ovRunHistory = []; _ovHealStats = {}; _ovFlakyTests = null; }
}

async function renderDashboardOverview(main) {
  await _loadOverviewData();

  // ── 데이터 수집 ──
  const ps = pipelineState || {};
  const psStep = ps.step || '-';
  const psStatus = ps.status || (psStep === 'done' ? 'done' : (psStep !== '-' && psStep !== 'init' ? 'running' : 'idle'));
  const psResult = ps.execution_result || {};
  const psPassed = psResult.passed || 0;
  const psFailed = psResult.failed || 0;
  const psTotal = psResult.total || 0;

  const bs = (batchState || {}).parallel_state || {};
  const bsStatus = bs.status || (bs.step === 'done' ? 'done' : 'idle');
  const bsResult = bs.execution_result || {};
  const bsPassed = bsResult.passed || 0;
  const bsFailed = bsResult.failed || 0;
  const bsTotal = bsResult.total || 0;

  const rptCount = (reportsList || []).length;
  const history = _ovRunHistory || [];
  const healStats = _ovHealStats || {};
  const patterns = healStats.patterns || {};
  const flakyData = _ovFlakyTests || null;

  // 최근 실행
  const lastRun = history.length > 0 ? history[history.length - 1] : null;
  const totalTests = lastRun ? (lastRun.total || 0) : 0;
  const totalPassed = lastRun ? (lastRun.passed || 0) : 0;
  const totalFailed = lastRun ? (lastRun.failed || 0) : 0;
  // skipped: run_history → pipeline state → batch state → quickState 순으로 폴백
  const _rhSkipped = lastRun ? (lastRun.skipped ?? null) : null;
  const _quickExecSkipped = (quickState && quickState.execution_result != null)
    ? (quickState.execution_result.skipped ?? null) : null;
  const _stateSkipped = psResult.skipped ?? bsResult.skipped ?? _quickExecSkipped ?? 0;
  const totalSkipped = _rhSkipped !== null ? _rhSkipped : _stateSkipped;
  const passRate = totalTests > 0 ? Math.round(totalPassed / totalTests * 1000) / 10 : 0;

  // 상태 헬퍼
  function sLabel(s) {
    if (s === 'done') return '완료';
    if (s === 'idle') return '대기';
    if (s === 'testing') return '실행 중';
    if (s === 'generating') return '생성 중';
    if (s === 'ready') return '준비됨';
    return s;
  }

  // ── 1. Hero Section: 대형 도넛 + 핵심 지표 ──
  const donutPct = passRate;
  const donutColor = totalFailed === 0 ? 'var(--approved-color)' : donutPct >= 80 ? 'var(--pending-color)' : 'var(--revision-color)';
  // 3-segment donut: circumference = 2π*42 ≈ 264
  const _C = 264;
  const _passedArc  = totalTests > 0 ? (totalPassed  / totalTests) * _C : 0;
  const _failedArc  = totalTests > 0 ? (totalFailed  / totalTests) * _C : 0;
  const _skippedArc = totalTests > 0 ? (totalSkipped / totalTests) * _C : 0;

  // 도넛 범례: 파이프라인별 표시
  const lastRunPipeline = lastRun ? ({parallel:'병렬', quick:'빠른 실행', single:'단일'}[lastRun.pipeline] || lastRun.pipeline) : '';
  const lastRunTime = lastRun ? (lastRun.timestamp || '').split(' ')[1] || '' : '';

  const heroHtml = totalTests > 0 ? `
    <div class="oax-hero">
      <div class="oax-hero-left">
        <div class="oax-donut-wrap">
          <svg viewBox="-5 -5 110 110" class="oax-donut">
            <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(140,120,220,0.08)" stroke-width="5"/>
            ${_passedArc  > 0 ? `<circle cx="50" cy="50" r="42" fill="none" stroke="var(--approved-color)" stroke-width="5" stroke-dasharray="${_passedArc} ${_C-_passedArc}" stroke-dashoffset="66" stroke-linecap="butt" style="filter:drop-shadow(0 0 4px var(--approved-color))"/>` : ''}
            ${_failedArc  > 0 ? `<circle cx="50" cy="50" r="42" fill="none" stroke="var(--revision-color)" stroke-width="5" stroke-dasharray="${_failedArc} ${_C-_failedArc}" stroke-dashoffset="${66-_passedArc}" stroke-linecap="butt" style="filter:drop-shadow(0 0 4px var(--revision-color))"/>` : ''}
            ${_skippedArc > 0 ? `<circle cx="50" cy="50" r="42" fill="none" stroke="#a855f7" stroke-width="5" stroke-dasharray="${_skippedArc} ${_C-_skippedArc}" stroke-dashoffset="${66-_passedArc-_failedArc}" stroke-linecap="butt" style="filter:drop-shadow(0 0 4px #a855f7)"/>` : ''}
          </svg>
          <div class="oax-donut-center">
            <div class="oax-donut-pct">${passRate}<span class="oax-donut-unit">%</span></div>
            <div class="oax-donut-label">Pass Rate</div>
          </div>
        </div>
        <div class="oax-hero-detail">
          <div class="oax-hero-context">${lastRunPipeline} 실행 · ${lastRunTime}</div>
          <div class="oax-hero-stats">
            <div class="oax-hero-stat">
              <div class="oax-hero-stat-val">${totalTests}</div>
              <div class="oax-hero-stat-label">Total</div>
            </div>
            <div class="oax-hero-stat">
              <div class="oax-hero-stat-val" style="color:var(--approved-color)">${totalPassed}</div>
              <div class="oax-hero-stat-label">Passed</div>
            </div>
            <div class="oax-hero-stat">
              <div class="oax-hero-stat-val" style="color:${totalFailed > 0 ? 'var(--revision-color)' : 'var(--text-dim)'}">${totalFailed}</div>
              <div class="oax-hero-stat-label">Failed</div>
            </div>
            ${totalSkipped > 0 ? `<div class="oax-hero-stat">
              <div class="oax-hero-stat-val" style="color:#a855f7">${totalSkipped}</div>
              <div class="oax-hero-stat-label">Skipped</div>
            </div>` : ''}
          </div>
          <div class="oax-hero-legend">
            <span class="oax-legend-item"><span class="oax-legend-dot" style="background:var(--approved-color)"></span>통과</span>
            <span class="oax-legend-item"><span class="oax-legend-dot" style="background:var(--revision-color)"></span>실패</span>
            <span class="oax-legend-item"><span class="oax-legend-dot" style="background:var(--pending-color)"></span>경고 (80%↑)</span>
          </div>
        </div>
      </div>
      <div class="oax-hero-right">
        ${_buildTrendChart(history)}
      </div>
    </div>` : '';

  // ── 2. KPI 카드 행 ──
  const kpiHtml = `
    <div class="oax-kpi-row">
      <div class="oax-kpi" onclick="selectView('single_pipeline')">
        <div class="oax-kpi-icon" style="color:var(--accent)">◆</div>
        <div class="oax-kpi-body">
          <div class="oax-kpi-label">Single Pipeline</div>
          <div class="oax-kpi-val" style="color:${psStatus === 'done' ? 'var(--approved-color)' : psStatus === 'idle' ? 'var(--text-dim)' : 'var(--pending-color)'}">${sLabel(psStatus)}</div>
        </div>
        <div class="oax-kpi-meta">${psStatus === 'done' && psTotal > 0 ? psPassed + '/' + psTotal : ''}</div>
      </div>
      <div class="oax-kpi" onclick="selectView('parallel_pipeline')">
        <div class="oax-kpi-icon" style="color:var(--delib-accent)">◆</div>
        <div class="oax-kpi-body">
          <div class="oax-kpi-label">Parallel Pipeline</div>
          <div class="oax-kpi-val" style="color:${bsStatus === 'done' ? 'var(--approved-color)' : bsStatus === 'idle' ? 'var(--text-dim)' : 'var(--pending-color)'}">${sLabel(bsStatus)}</div>
        </div>
        <div class="oax-kpi-meta">${bsStatus === 'done' && bsTotal > 0 ? bsPassed + '/' + bsTotal : ''}</div>
      </div>
      <div class="oax-kpi" onclick="selectView('reports')">
        <div class="oax-kpi-icon" style="color:var(--senior-accent)">◆</div>
        <div class="oax-kpi-body">
          <div class="oax-kpi-label">Reports</div>
          <div class="oax-kpi-val">${rptCount}<span style="font-size:12px;opacity:0.4;margin-left:3px;">건</span></div>
        </div>
        <div class="oax-kpi-meta">${rptCount > 0 ? esc(reportsList[0].name).substring(0, 20) : ''}</div>
      </div>
    </div>`;

  // ── 3. 하단 그리드 ──
  const groups = pagesData.groups || [];

  // ── ③ 힐링 상황판 ──
  let healPanelHtml = '';
  const healCtx = ps.heal_context || {};
  if (psStep === 'heal_needed' || psStep === 'heal_failed') {
    const hCount = healCtx.heal_count || ps.heal_count || 0;
    const maxHeals = 3;
    const failGroups = healCtx.failure_groups || {};
    const totalFailCount = healCtx.failure_count || 0;
    if (psStep === 'heal_failed') {
      healPanelHtml = `<div class="heal-panel heal-panel--failed">
        <div class="heal-panel-title">⚠ 수동 수정 필요</div>
        <div class="heal-panel-desc">힐링 ${maxHeals}회 모두 시도했으나 실패했습니다. 테스트 파일을 직접 수정해주세요.</div>
      </div>`;
    } else {
      const groupBadges = Object.entries(failGroups).map(([type, tests]) =>
        `<span class="heal-group-badge">${esc(type)} ${Array.isArray(tests) ? tests.length : tests}건</span>`
      ).join('');
      const dots = Array.from({length: maxHeals}, (_, i) =>
        `<div class="heal-progress-dot ${i < hCount ? 'heal-progress-dot--done' : ''}"></div>`
      ).join('');
      healPanelHtml = `<div class="heal-panel">
        <div class="heal-panel-title">힐링 진행 중</div>
        <div class="heal-panel-progress">
          <span>${hCount}/${maxHeals}회</span>
          <div class="heal-progress-track">${dots}</div>
        </div>
        <div class="heal-panel-desc">실패 ${totalFailCount}건 ${groupBadges}</div>
      </div>`;
    }
  }

  // ── ④ Flaky Test 카드 ──
  let flakyHtml = '';
  {
    const flakyList = (flakyData && flakyData.flaky) ? flakyData.flaky : [];
    if (flakyList.length > 0) {
      const rows = flakyList.slice(0, 6).map(f => {
        const dots = (f.recent || []).slice(-5).map(r =>
          `<span class="flaky-dot flaky-dot--${r}"></span>`
        ).join('');
        const rateColor = 'var(--pending-color)';
        return `<div class="flaky-row">
          <span class="flaky-name">${esc(f.test_id)}</span>
          <div class="flaky-dots">${dots}</div>
          <span class="flaky-rate" style="color:${rateColor}">${Math.round(f.pass_rate * 100)}%</span>
        </div>`;
      }).join('');
      flakyHtml = `<div class="oax-card">
        <div class="oax-card-title" style="color:var(--pending-color)">Flaky 테스트
          <span class="oax-card-badge" style="color:var(--pending-color);background:rgba(251,191,36,0.08)">${flakyList.length}건</span>
        </div>
        ${rows}
      </div>`;
    }
  }

  // Welcome (no data)
  const hasAnyData = totalTests > 0 || history.length > 0 || groups.length > 0;
  const welcomeHtml = !hasAnyData ? `
    <div class="oax-card" style="text-align:center;padding:48px 24px;">
      <div style="font-size:40px;margin-bottom:16px;">🚀</div>
      <h3 style="font-size:18px;font-weight:700;margin-bottom:8px;">첫 번째 테스트를 실행해 보세요</h3>
      <p style="color:var(--text-dim);font-size:13px;margin-bottom:24px;">URL을 등록하고 파이프라인을 실행하면 테스트가 자동 생성됩니다.</p>
      <div style="display:flex;gap:12px;justify-content:center;">
        <button class="action-btn action-btn-primary" onclick="selectView('single_pipeline')">단일 파이프라인</button>
        <button class="action-btn action-btn-primary" onclick="selectView('parallel_pipeline')">병렬 파이프라인</button>
      </div>
    </div>` : '';

  // 로그
  const logHtml = `
    <div class="oax-card oax-log-section">
      <div class="oax-card-title">
        Recent Logs
        <div style="margin-left:auto;display:flex;gap:4px;align-items:center;">
          <button class="ov-log-tab active" data-log="run_qa.txt">단일</button>
          <button class="ov-log-tab" data-log="run_parallel.txt">병렬</button>
          <button class="ov-log-tab" data-log="quick_run.txt">빠른</button>
          <button class="ov-log-refresh" id="ov-log-refresh" title="새로고침">&#8635;</button>
        </div>
      </div>
      <div class="ov-log-box" id="ov-log-content">로그 로딩 중...</div>
    </div>`;

  // ── 조합 ── (이전 로그 내용+스크롤 보존으로 깜빡임 방지)
  const _prevLogEl = document.getElementById('ov-log-content');
  const _prevLogContent = _prevLogEl?.textContent;
  // null = 첫 로드(→맨아래로), 숫자 = 이전 스크롤 위치(→유지)
  const _prevLogScrollTop = _prevLogEl ? _prevLogEl.scrollTop : null;

  main.innerHTML = `
    <div class="ov-wrap">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
        <h2 class="ov-heading" style="margin-bottom:0;">Dashboard</h2>
        <button class="action-btn action-btn-danger" onclick="resetDashboard()" style="font-size:11px;padding:5px 12px;">대시보드 초기화</button>
      </div>
      ${welcomeHtml}
      ${healPanelHtml}
      ${heroHtml}
      ${hasAnyData ? kpiHtml : ''}
      ${hasAnyData && flakyHtml ? `<div class="oax-grid-3"><div class="oax-grid-col">${flakyHtml}</div></div>` : ''}
      ${logHtml}
    </div>`;

  // 이전 로그 내용+스크롤 즉시 복원 (플래시 방지)
  if (_prevLogContent && _prevLogContent !== '로그 로딩 중...') {
    const logBoxInit = document.getElementById('ov-log-content');
    if (logBoxInit) {
      logBoxInit.textContent = _prevLogContent;
      if (_prevLogScrollTop !== null) logBoxInit.scrollTop = _prevLogScrollTop;
    }
  }

  // 로그 이벤트
  const logBox = document.getElementById('ov-log-content');
  let _currentLogFile = _uiState.overviewLogTab || 'run_qa.txt';

  // 이전 자동 갱신 타이머 클리어 (orphan interval 방지)
  if (_ovLogAutoRefresh) { clearInterval(_ovLogAutoRefresh); _ovLogAutoRefresh = null; }

  async function loadLog(logName) {
    _currentLogFile = logName;
    _uiState.overviewLogTab = logName;
    const isFirstLoad = _prevLogScrollTop === null;
    const currentScrollTop = logBox.scrollTop;
    // 맨 아래 기준: 첫 로드이거나 이미 맨 아래에 있는 경우
    const isAtBottom = isFirstLoad || (logBox.scrollHeight - currentScrollTop - logBox.clientHeight < 40);
    try {
      const res = await fetch('/api/run_log', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({log: logName}) });
      const data = await res.json();
      if (data.ok && data.log) {
        const lines = data.log.split('\\n');
        logBox.textContent = lines.slice(-50).join('\\n') || '(빈 로그)';
      } else { logBox.textContent = '(로그 없음)'; }
    } catch(e) { logBox.textContent = '(로그 로드 실패)'; }
    // 첫 로드 또는 맨 아래였으면 최신 로그 따라가기, 아니면 위치 고정
    if (isAtBottom) {
      logBox.scrollTop = logBox.scrollHeight;
    } else {
      logBox.scrollTop = currentScrollTop;
    }
  }

  main.querySelectorAll('.ov-log-tab').forEach(btn => {
    if (btn.dataset.log === _currentLogFile) btn.classList.add('active');
    else btn.classList.remove('active');
    btn.addEventListener('click', () => {
      main.querySelectorAll('.ov-log-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      loadLog(btn.dataset.log);
    });
  });
  document.getElementById('ov-log-refresh').addEventListener('click', () => loadLog(_currentLogFile));

  const isRunning = (psStatus !== 'done' && psStatus !== 'idle') || (bsStatus !== 'done' && bsStatus !== 'idle');
  if (isRunning) _ovLogAutoRefresh = setInterval(() => loadLog(_currentLogFile), 5000);
  loadLog(_currentLogFile);
}

// ── 트렌드 차트 빌더 ──
function _buildTrendChart(history) {
  if (!history || history.length === 0) return '<div class="oax-trend-empty">실행 이력 없음</div>';

  const finalOnly = [];
  for (let i = 0; i < history.length; i++) {
    const cur = history[i];
    const next = history[i + 1];
    const curKey = cur.pipeline + '|' + (cur.group || (cur.groups || []).sort().join(','));
    const nextKey = next ? next.pipeline + '|' + (next.group || (next.groups || []).sort().join(',')) : null;
    if (curKey !== nextKey) finalOnly.push(cur);
  }
  const recent = finalOnly.slice(-8);

  // SVG 라인 차트
  const w = 320, h = 120, padX = 28, padY = 18, padBot = 14;
  const chartH = h - padY - padBot;
  const stepX = recent.length > 1 ? (w - padX * 2) / (recent.length - 1) : 0;
  let points = '';
  let areaPoints = `${padX},${padY + chartH} `;
  let dots = '';
  let labels = '';
  let pctLabels = '';

  // 겹침 방지: 이전 라벨의 y좌표 추적
  let prevLabelY = -100;
  const minLabelGap = 12; // px 최소 간격

  // 시간 라벨: 5개 이상이면 간격 두고 표시
  const showEveryN = recent.length > 5 ? 2 : 1;

  recent.forEach((r, i) => {
    const x = padX + stepX * i;
    const rate = r.pass_rate || 0;
    const rDisplay = rate === 100 ? '100' : (Math.floor(rate * 10) / 10).toFixed(1);
    const y = padY + chartH - (rate / 100) * chartH;
    points += `${x},${y} `;
    areaPoints += `${x},${y} `;
    const ts = (r.timestamp || '').split(' ')[1] || '';
    const shortTs = ts.substring(0, 5);
    const color = rate === 100 ? 'var(--approved-color)' : rate >= 80 ? 'var(--pending-color)' : 'var(--revision-color)';
    const _skippedTip = r.skipped ? ` | 스킵:${r.skipped}` : '';
    dots += `<circle cx="${x}" cy="${y}" r="3.5" fill="${color}" stroke="rgba(8,7,27,0.6)" stroke-width="1.5" style="filter:drop-shadow(0 0 3px ${color})"><title>${rDisplay}% | 통과:${r.passed||0} 실패:${r.failed||0}${_skippedTip}</title></circle>`;

    // 퍼센트 라벨 — 이전과 Y좌표가 가까우면 위/아래로 오프셋
    let labelY = y - 8;
    if (Math.abs(labelY - prevLabelY) < minLabelGap) {
      labelY = prevLabelY < y ? y + 14 : y - 8 - minLabelGap + Math.abs(labelY - prevLabelY);
    }
    pctLabels += `<text x="${x}" y="${labelY}" text-anchor="middle" fill="${color}" font-size="8" font-weight="600" font-family="Inter">${rDisplay}%</text>`;
    prevLabelY = labelY;

    // 시간 라벨 — 첫/마지막은 항상, 나머지는 간격에 따라
    if (i === 0 || i === recent.length - 1 || i % showEveryN === 0) {
      labels += `<text x="${x}" y="${h - 2}" text-anchor="middle" fill="var(--text-dim)" font-size="7" font-family="Inter">${shortTs}</text>`;
    }
  });
  areaPoints += `${padX + stepX * (recent.length - 1)},${padY + chartH}`;

  // Y축 가이드라인
  const gridLines = [100, 80, 60].map(v => {
    const y = padY + chartH - (v / 100) * chartH;
    return `<line x1="${padX}" y1="${y}" x2="${w - padX}" y2="${y}" stroke="rgba(140,120,220,0.06)" stroke-width="0.5"/>`;
  }).join('');

  const lastDur = recent.length > 0 && recent[recent.length - 1].duration_sec ? Math.round(recent[recent.length - 1].duration_sec) + 's' : '-';
  const firstPass = recent.length > 0 && recent[recent.length - 1].first_pass ? 'First Pass' : (recent.length > 0 ? (recent[recent.length - 1].heal_count || 0) + '회 힐링' : '');

  return `
    <div class="oax-trend">
      <div class="oax-trend-header">
        <span class="oax-trend-title">Run History</span>
      </div>
      <svg viewBox="0 0 ${w} ${h}" class="oax-trend-svg">
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="var(--accent)" stop-opacity="0.2"/>
            <stop offset="100%" stop-color="var(--accent)" stop-opacity="0"/>
          </linearGradient>
        </defs>
        ${gridLines}
        <polygon points="${areaPoints}" fill="url(#areaGrad)"/>
        <polyline points="${points}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter:drop-shadow(0 0 4px var(--accent-glow))"/>
        ${dots}
        ${pctLabels}
        ${labels}
      </svg>
      <div class="oax-trend-footer">
        <span>${lastDur} · ${firstPass}</span>
        <span class="oax-trend-legend">
          <span class="oax-legend-item"><span class="oax-legend-dot" style="background:var(--approved-color)"></span>100%</span>
          <span class="oax-legend-item"><span class="oax-legend-dot" style="background:var(--pending-color)"></span>80%↑</span>
          <span class="oax-legend-item"><span class="oax-legend-dot" style="background:var(--revision-color)"></span>80%↓</span>
        </span>
      </div>
    </div>`;
}
