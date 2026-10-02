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
  const groups = pagesData.groups || [];
  const healStats = _ovHealStats || {};
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
  const recentRuns = history.slice(-10);
  const recentTotal = recentRuns.reduce((sum, run) => sum + (run.total || 0), 0);
  const recentPassed = recentRuns.reduce((sum, run) => sum + (run.passed || 0), 0);
  const recentPassRate = recentTotal ? Math.round(recentPassed / recentTotal * 100) : 0;
  const recentHealCount = recentRuns.reduce((sum, run) => sum + (run.heal_count || 0), 0);

  // 상태 헬퍼
  function sLabel(s) {
    if (s === 'done') return '완료';
    if (s === 'idle') return '대기';
    if (s === 'testing') return '실행 중';
    if (s === 'generating') return '생성 중';
    if (s === 'ready') return '준비됨';
    return s;
  }

  // ── 핵심 지표 ──
  const lastRunLabel = !lastRun ? '실행 기록 없음' : totalFailed > 0 ? '실패' : totalSkipped > 0 ? '중단' : '통과';
  const lastRunClass = totalFailed > 0 ? 'fail' : totalSkipped > 0 ? 'warn' : 'pass';
  const lastRunTime = lastRun ? (lastRun.timestamp || '').slice(5, 16) : '';
  const heroHtml = `<section class="ov-summary-row" aria-label="요약">
    <div class="ov-summary-item"><div class="ov-summary-label">마지막 실행</div><div class="ov-summary-value"><span class="ov-result ${lastRunClass}">${lastRunLabel}</span></div><div class="ov-summary-meta">${lastRun ? `${totalTests}건 중 ${totalPassed}건 통과 · 실패 ${totalFailed} · 건너뜀 ${totalSkipped} · ${Math.round(lastRun.duration_sec || 0)}초` : '실행 이력이 없습니다'}</div></div>
    <div class="ov-summary-item"><div class="ov-summary-label">최근 10회 통과율</div><div class="ov-summary-value">${recentTotal ? `${recentPassRate}%` : '—'}</div><div class="ov-summary-meta">통과 ${recentPassed} · 전체 ${recentTotal}</div></div>
    <div class="ov-summary-item"><div class="ov-summary-label">등록된 페이지</div><div class="ov-summary-value">${groups.length}</div><div class="ov-summary-meta">페이지 그룹</div></div>
    <div class="ov-summary-item"><div class="ov-summary-label">자동 복구(힐링)</div><div class="ov-summary-value">${recentHealCount}</div><div class="ov-summary-meta">최근 ${recentRuns.length}회 기준</div></div>
  </section>`;

  const recentRows = [...history].reverse().slice(0, 6).map(run => {
    const typeLabel = { parallel: '병렬 파이프라인', quick: '빠른 실행', single: '단일 파이프라인' }[run.pipeline] || run.pipeline || '—';
    const targets = run.group ? [run.group] : (run.groups || []);
    const result = (run.failed || 0) > 0 ? ['실패', 'fail'] : (run.skipped || 0) > 0 ? ['중단', 'warn'] : ['통과', 'pass'];
    const timestamp = (run.timestamp || '').slice(5, 16) || '—';
    const duration = run.duration_sec ? `${Math.round(run.duration_sec)}초` : '—';
    return `<tr><td><span class="ov-time">${esc(timestamp)}</span></td><td>${esc(typeLabel)}</td><td>${esc(targets.join(' · ') || '—')}</td><td><span class="ov-result ${result[1]}">${result[0]}</span></td><td class="ov-num">${run.passed || 0}/${run.total || 0}</td><td class="ov-num">${esc(duration)}</td></tr>`;
  }).join('');
  const recentTableHtml = `<section class="oax-card"><div class="oax-card-title">최근 실행 <button type="button" class="ov-history-link" onclick="selectView('history')">전체 기록 보기</button></div>${recentRows ? `<div class="ov-table-wrap"><table class="ov-table"><thead><tr><th>시작</th><th>종류</th><th>대상</th><th>결과</th><th style="text-align:right;">통과</th><th style="text-align:right;">소요</th></tr></thead><tbody>${recentRows}</tbody></table></div>` : `<div class="ov-table-empty">최근 실행 이력이 없습니다.</div>`}</section>`;

  const quickStatus = quickState || {};
  const quickStep = quickStatus.status || quickStatus.step || 'idle';
  const teamCount = (lastData?.team_sessions || []).length;
  const statusRow = (label, value, view, meta = '') => `<button type="button" class="ov-status-row" onclick="selectView('${view}')"><span>${label}</span><span class="ov-status-value">${value}${meta ? `<span class="ov-status-meta">${meta}</span>` : ''}</span></button>`;
  const statusHtml = `<section class="oax-card"><h3 class="oax-card-title">파이프라인 상태</h3><div class="ov-status-list">
    ${statusRow('단일 파이프라인', sLabel(psStatus), 'single_pipeline', psStatus === 'done' && psTotal ? `${psPassed}/${psTotal}` : '')}
    ${statusRow('병렬 파이프라인', sLabel(bsStatus), 'parallel_pipeline', bsStatus === 'done' && bsTotal ? `${bsPassed}/${bsTotal}` : '')}
    ${statusRow('빠른 실행', sLabel(quickStep), 'quick_run', quickStep === 'done' && quickStatus.execution_result?.total ? `${quickStatus.execution_result.passed || 0}/${quickStatus.execution_result.total}` : '')}
    ${statusRow('리포트', `${rptCount}건`, 'reports')}
    <div class="ov-status-row"><span>팀 토론</span><span class="ov-status-value">${teamCount ? `진행 중 ${teamCount}건` : '토론 없음'}</span></div>
  </div></section>`;

  const trendHtml = `<section class="oax-card"><h3 class="oax-card-title">통과율 추이</h3>${_buildTrendChart(history)}</section>`;
  const logHtml = `
    <section class="oax-card oax-log-section">
      <div class="oax-card-title">최근 로그
        <div style="margin-left:auto;display:flex;gap:4px;align-items:center;">
          <button class="ov-log-tab active" data-log="run_qa.txt">단일</button>
          <button class="ov-log-tab" data-log="run_parallel.txt">병렬</button>
          <button class="ov-log-tab" data-log="quick_run.txt">빠른</button>
          <button class="ov-log-refresh" id="ov-log-refresh" title="새로고침" aria-label="로그 새로고침">&#8635;</button>
        </div>
      </div>
      <div class="ov-log-box" id="ov-log-content">로그 로딩 중...</div>
    </section>`;

  // ── 3. 하단 그리드 ──
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
        <div class="heal-panel-title">수동 수정 필요</div>
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
          `<span class="flaky-dot flaky-dot--${r}">${r === 'pass' ? '통과' : r === 'fail' ? '실패' : esc(r)}</span>`
        ).join('');
        return `<div class="flaky-row">
          <span class="flaky-name">${esc(f.test_id)}</span>
          <div class="flaky-dots">${dots}</div>
          <span class="flaky-rate">${Math.round(f.pass_rate * 100)}%</span>
        </div>`;
      }).join('');
      flakyHtml = `<div class="oax-card">
        <div class="oax-card-title">간헐적 실패 테스트
          <span class="oax-card-badge">${flakyList.length}건</span>
        </div>
        ${rows}
      </div>`;
    }
  }

  // Welcome (no data)
  const hasAnyData = totalTests > 0 || history.length > 0 || groups.length > 0;
  const welcomeHtml = !hasAnyData ? `
    <div class="oax-card" style="text-align:center;padding:48px 24px;">
      <div class="empty-icon" aria-hidden="true"><svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="8" y="6" width="24" height="28" rx="3"></rect><line x1="13" y1="14" x2="27" y2="14"></line><line x1="13" y1="20" x2="27" y2="20"></line><line x1="13" y1="26" x2="21" y2="26"></line></svg></div>
      <h3 style="font-size:15px;font-weight:600;margin-bottom:0;">첫 번째 테스트를 실행해 보세요</h3>
      <p style="color:var(--text-2);font-size:13px;margin-bottom:8px;">URL을 등록하고 파이프라인을 실행하면 테스트가 자동 생성됩니다.</p>
      <div style="display:flex;gap:12px;justify-content:center;">
        <button class="action-btn action-btn-primary" onclick="selectView('single_pipeline')">단일 파이프라인</button>
        <button class="action-btn" onclick="selectView('parallel_pipeline')">병렬 파이프라인</button>
      </div>
    </div>` : '';

  // ── 조합 ── (이전 로그 내용+스크롤 보존으로 깜빡임 방지)
  const _prevLogEl = document.getElementById('ov-log-content');
  const _prevLogContent = _prevLogEl?.textContent;
  // null = 첫 로드(→맨아래로), 숫자 = 이전 스크롤 위치(→유지)
  const _prevLogScrollTop = _prevLogEl ? _prevLogEl.scrollTop : null;

  main.innerHTML = `
    <div class="ov-wrap">
      <div class="ov-head">
        <div class="ov-head-copy"><h2 class="ov-heading">대시보드</h2><p class="ov-subtitle">${lastRun ? `마지막 실행 ${esc(lastRun.timestamp || '')}` : '아직 실행한 기록이 없습니다'}</p></div>
        <button class="ov-reset-btn" onclick="resetDashboard()">대시보드 초기화</button>
      </div>
      ${heroHtml}
      ${welcomeHtml}
      ${healPanelHtml}
      <div class="ov-main-grid">
        <div class="ov-col">${recentTableHtml}${trendHtml}${flakyHtml}</div>
        <div class="ov-col">${statusHtml}${logHtml}</div>
      </div>
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
    const ts = (r.timestamp || '').split(' ')[1] || '';
    const shortTs = ts.substring(0, 5);
    const color = rate === 100 ? 'var(--approved-color)' : rate >= 80 ? 'var(--pending-color)' : 'var(--revision-color)';
    const _skippedTip = r.skipped ? ` · 건너뜀 ${r.skipped}` : '';
    dots += `<circle cx="${x}" cy="${y}" r="3.5" fill="${color}" stroke="var(--surface)" stroke-width="1.5"><title>${rDisplay}% · 통과 ${r.passed||0} · 실패 ${r.failed||0}${_skippedTip}</title></circle>`;

    // 퍼센트 라벨 — 이전과 Y좌표가 가까우면 위/아래로 오프셋
    let labelY = y - 8;
    if (Math.abs(labelY - prevLabelY) < minLabelGap) {
      labelY = prevLabelY < y ? y + 14 : y - 8 - minLabelGap + Math.abs(labelY - prevLabelY);
    }
    pctLabels += `<text x="${x}" y="${labelY}" text-anchor="middle" fill="${color}" font-size="8" font-weight="600" font-family="'IBM Plex Sans KR', sans-serif">${rDisplay}%</text>`;
    prevLabelY = labelY;

    // 시간 라벨 — 첫/마지막은 항상, 나머지는 간격에 따라
    if (i === 0 || i === recent.length - 1 || i % showEveryN === 0) {
      labels += `<text x="${x}" y="${h - 2}" text-anchor="middle" fill="var(--text-2)" font-size="7" font-family="'JetBrains Mono', monospace">${shortTs}</text>`;
    }
  });

  // Y축 가이드라인
  const gridLines = [100, 80, 60].map(v => {
    const y = padY + chartH - (v / 100) * chartH;
    return `<line x1="${padX}" y1="${y}" x2="${w - padX}" y2="${y}" stroke="var(--border)" stroke-width="0.75"/>`;
  }).join('');

  const lastDur = recent.length > 0 && recent[recent.length - 1].duration_sec ? Math.round(recent[recent.length - 1].duration_sec) + '초' : '—';
  const firstPass = recent.length > 0 && recent[recent.length - 1].first_pass ? '첫 실행 통과' : (recent.length > 0 ? (recent[recent.length - 1].heal_count || 0) + '회 복구' : '');

  return `
    <div class="oax-trend">
      <svg viewBox="0 0 ${w} ${h}" class="oax-trend-svg">
        <defs><g id="areaGrad"></g></defs>
        ${gridLines}
        <polyline points="${points}" fill="none" stroke="var(--approved-color)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        ${dots}
        ${pctLabels}
        ${labels}
      </svg>
      <div class="oax-trend-footer">
        <span>${lastDur} · ${firstPass}</span>
        <span class="oax-trend-legend">
          <span class="oax-legend-item ov-result pass"><span class="oax-legend-dot" style="background:var(--approved-color)"></span>통과</span>
          <span class="oax-legend-item ov-result warn"><span class="oax-legend-dot" style="background:var(--pending-color)"></span>주의</span>
          <span class="oax-legend-item ov-result fail"><span class="oax-legend-dot" style="background:var(--revision-color)"></span>실패</span>
        </span>
      </div>
    </div>`;
}
