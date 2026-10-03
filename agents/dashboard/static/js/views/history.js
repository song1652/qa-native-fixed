// ── History View ──
async function renderHistory(main) {
  let history = [];
  try {
    history = await fetch('/api/run_history').then(r => r.json()) || [];
  } catch(e) { history = []; }

  if (history.length === 0) {
    main.innerHTML = `
      <div class="hist-wrap">
        <h2 class="hist-heading">실행 기록</h2>
        <div class="hist-empty">
          <div class="hist-empty-icon" aria-hidden="true"><svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="8" y="6" width="24" height="28" rx="3"></rect><path d="M13 14h14M13 20h14M13 26h8"></path></svg></div>
          <div class="hist-empty-text">실행 이력이 없습니다. 파이프라인을 실행하면 이력이 쌓입니다.</div>
        </div>
      </div>`;
    return;
  }

  // ── 필터 상태 ──
  if (!_uiState._histFilter) _uiState._histFilter = { type: 'all', group: 'all' };
  const filter = _uiState._histFilter;

  // 그룹 목록 추출
  const allGroups = new Set();
  history.forEach(r => {
    if (r.group) allGroups.add(r.group);
    (r.groups || []).forEach(g => allGroups.add(g));
  });

  // 필터 적용
  let filtered = [...history].reverse(); // 최신 먼저
  if (filter.type !== 'all') {
    filtered = filtered.filter(r => r.pipeline === filter.type);
  }
  if (filter.group !== 'all') {
    filtered = filtered.filter(r =>
      r.group === filter.group || (r.groups || []).includes(filter.group)
    );
  }

  // ── 요약 통계 ──
  const total = history.length;
  const avgRate = total > 0
    ? Math.round(history.reduce((s, r) => s + (r.pass_rate || 0), 0) / total * 10) / 10
    : 0;
  const fpCount = history.filter(r => r.first_pass).length;
  const totalHeals = history.reduce((s, r) => s + (r.heal_count || 0), 0);

  const fpColor = fpCount / total >= 0.8 ? 'var(--approved-color)'
    : fpCount / total >= 0.5 ? 'var(--pending-color)' : 'var(--revision-color)';
  const rateColor = avgRate >= 95 ? 'var(--approved-color)'
    : avgRate >= 80 ? 'var(--pending-color)' : 'var(--revision-color)';

  const statsHtml = `
    <div class="hist-stat-row">
      <div class="hist-stat">
        <div class="hist-stat-label">총 실행 수</div>
        <div class="hist-stat-val">${total}</div>
      </div>
      <div class="hist-stat">
        <div class="hist-stat-label">평균 통과율</div>
        <div class="hist-stat-val" style="color:${rateColor}">${avgRate}%</div>
      </div>
      <div class="hist-stat">
        <div class="hist-stat-label">첫 실행 통과</div>
        <div class="hist-stat-val" style="color:${fpColor}">${fpCount}<span style="font-size:14px;opacity:0.5">/${total}</span></div>
      </div>
      <div class="hist-stat">
        <div class="hist-stat-label">총 힐링 횟수</div>
        <div class="hist-stat-val" style="color:var(--accent)">${totalHeals}</div>
      </div>
    </div>`;

  // ── 필터 바 ──
  const typeFilters = ['all', 'single', 'parallel', 'quick'].map(t => {
    const label = { all: '전체', single: '단일', parallel: '병렬', quick: '빠른 실행' }[t];
    return `<button class="hist-filter-btn ${filter.type === t ? 'active' : ''}"
      onclick="_histSetFilter('type','${t}')">${label}</button>`;
  }).join('');

  const groupFilters = ['all', ...[...allGroups]].map(g => {
    const label = g === 'all' ? '전체 그룹' : g;
    return `<button class="hist-filter-btn ${filter.group === g ? 'active' : ''}"
      onclick="_histSetFilter('group','${g}')">${label}</button>`;
  }).join('');

  const filterHtml = `
    <div class="hist-filter">
      <span class="hist-filter-label">유형</span>
      ${typeFilters}
      <span class="hist-filter-label" style="margin-left:8px;">그룹</span>
      ${groupFilters}
    </div>`;

  // ── 이력 카드 목록 ──
  const cardsHtml = filtered.length === 0
    ? `<div class="hist-empty"><div class="hist-empty-text">필터 조건에 맞는 이력이 없습니다.</div></div>`
    : filtered.map(r => _buildHistCard(r)).join('');

  main.innerHTML = `
    <div class="hist-wrap">
      <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:4px;">
        <h2 class="hist-heading" style="margin-bottom:0;">실행 기록</h2>
        <button class="action-btn" onclick="_histReset()" style="margin-left:auto;" title="실행 이력 전체 삭제">기록 초기화</button>
      </div>
      <p class="pipeline-subtitle">모든 실행의 결과와 힐링 횟수를 시간순으로 봅니다.</p>
      ${filterHtml}
      ${statsHtml}
      ${filtered.length ? `<div class="hist-table-wrap"><table class="hist-table"><thead><tr><th>시작</th><th>종류</th><th>대상</th><th>결과</th><th>통과 / 전체</th><th>통과율</th><th>힐링</th><th>소요</th></tr></thead><tbody id="hist-cards">${cardsHtml}</tbody></table></div>` : `<div id="hist-cards">${cardsHtml}</div>`}
    </div>`;
}

function _buildHistCard(r) {
  const ts = r.timestamp || '';
  const datePart = ts.split(' ')[0] || '';
  const timePart = ts.split(' ')[1] || '';
  const rate = r.pass_rate || 0;
  const rateColor = rate >= 95 ? 'var(--approved-color)'
    : rate >= 80 ? 'var(--pending-color)' : 'var(--revision-color)';

  // 배지
  let badge = '';
  if (r.first_pass) {
    badge = `<span class="hist-badge hist-badge--first">첫 실행 통과</span>`;
  } else if (r.heal_count > 0) {
    badge = `<span class="hist-badge hist-badge--heal">힐링 ${r.heal_count}회</span>`;
  } else {
    badge = `<span class="hist-badge hist-badge--type" style="opacity:0.4;">-</span>`;
  }
  const failedRun = r.failed > 0 || ['failed', 'error', 'timeout', 'timed_out', 'interrupted', 'cancelled', 'incomplete', 'heal_failed', 'heal_needed'].includes(r.status);
  const statusLabel = ['timeout', 'timed_out'].includes(r.status) ? '시간 초과' : ['interrupted', 'cancelled'].includes(r.status) ? '중단' : failedRun ? '실패' : '통과';
  const recovery = r.recovery || {};
  const recoveryHtml = failedRun ? `<div class="hist-recovery">${recovery.title ? `<strong>${esc(recovery.title)}</strong><br>` : ''}${esc(recovery.message || r.error || '실행 로그에서 오류 원인을 확인하세요.')}<br><span class="muted">${r.report_path ? '리포트: ' + esc(r.report_path) : '리포트 없음 · 실행 기록은 보존됩니다.'}</span></div>` : '';
  const failBadge = r.failed > 0
    ? `<span class="hist-badge hist-badge--fail">${r.failed}건 실패</span>` : '';

  const typeLabel = { parallel: '병렬', quick: '빠른 실행', single: '단일' }[r.pipeline] || r.pipeline || '-';
  const groups = r.group ? [r.group] : (r.groups || []);
  const groupTags = groups.map(g => `<span class="hist-group-tag">${esc(g)}</span>`).join(' ');
  const dur = r.duration_sec ? Math.round(r.duration_sec) + '초' : '-';

  return `<tr class="hist-card">
    <td class="hist-time">${esc(datePart)}<br><span class="muted">${esc(timePart)}</span></td>
    <td>${typeLabel}</td>
    <td>${groupTags || '—'}</td>
    <td><span class="hist-badge ${failedRun ? 'hist-badge--fail' : 'hist-badge--first'}">${statusLabel}</span> ${failedRun && r.first_pass ? '' : badge}${failBadge}${recoveryHtml}</td>
    <td class="hist-number">${r.passed || 0} / ${r.total || 0}</td>
    <td class="hist-number" style="color:${rateColor}">${rate}%</td>
    <td class="hist-number">${r.heal_count || 0}</td>
    <td class="hist-number">${dur}</td>
  </tr>`;
}

function _histSetFilter(key, val) {
  if (!_uiState._histFilter) _uiState._histFilter = { type: 'all', group: 'all' };
  _uiState._histFilter[key] = val;
  const main = document.getElementById('main');
  if (main) renderHistory(main);
}

async function _histReset() {
  if (!await safeConfirm('실행 이력을 전체 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.')) return;
  try {
    await fetch('/api/run_history/reset', { method: 'POST' });
    const main = document.getElementById('main');
    if (main) renderHistory(main);
  } catch(e) {
    alert('이력 초기화 실패: ' + e.message);
  }
}

