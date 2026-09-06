// ── Quick Run View ──
function renderQuickRun(main) {
  // 체크 상태 보존
  const prevChecked = {};
  document.querySelectorAll('.quick-group-cb').forEach(cb => { prevChecked[cb.value] = cb.checked; });
  // 로그 스크롤 위치 보존
  const _logArea = document.getElementById('run-quick-log');
  const _logScrollTop = _logArea ? _logArea.scrollTop : null;
  const _logScrollHeight = _logArea ? _logArea.scrollHeight : 0;
  const _logClientHeight = _logArea ? _logArea.clientHeight : 0;
  const _wasAtBottom = _logScrollTop === null || (_logScrollHeight - _logScrollTop - _logClientHeight < 40);

  const groups = generatedGroups || [];
  const execResult = quickState ? quickState.execution_result : null;

  let groupsHtml = '';
  if (groups.length) {
    groupsHtml = groups.map(g => {
      const checked = prevChecked[g.name] !== undefined ? prevChecked[g.name] : true;
      const staleWarn = g.stale_count ? `<span style="font-size:10px;color:var(--pending-color);margin-left:4px;" title="testcases와 불일치하는 잔여 파일 ${g.stale_count}개 있음 — 재생성 시 자동 정리됩니다">⚠ +${g.stale_count}</span>` : '';
      return `<label class="quick-group-item">
        <input type="checkbox" class="quick-group-cb" value="${esc(g.name)}" ${checked ? 'checked' : ''}>
        <span class="quick-group-name">${esc(g.name)}</span>
        <span class="quick-group-count">${g.file_count}개 파일${staleWarn}</span>
      </label>`;
    }).join('');
  } else {
    groupsHtml = '<div style="padding:12px;font-size:13px;color:var(--text-dim);">생성된 테스트 폴더가 없습니다. 먼저 병렬 파이프라인으로 테스트 코드를 생성하세요.</div>';
  }

  // 실행 결과 카드
  let resultHtml = '';
  if (execResult) {
    const allPass = execResult.failed === 0;
    const badgeCls = allPass ? 'pass' : 'fail';
    const badgeTxt = allPass ? 'ALL PASS' : `${execResult.failed} FAILED`;
    const groupResultsHtml = buildGroupResultsHtml(execResult.group_results || {}, 'quick');
    const quickStatus = quickState ? quickState.status : null;
    const healBannerHtml = (!allPass && quickStatus === 'heal_needed') ? `
      <div style="margin-top:12px;padding:10px 12px;background:rgba(255,165,0,0.1);border:1px solid var(--pending-color);border-radius:6px;font-size:12px;color:var(--pending-color);">
        ⚠ 힐링 필요 — 실패한 테스트를 수정한 후 다시 실행하세요. (힐링 ${execResult.heal_count || 0}/3회 완료)
      </div>` : (!allPass && quickStatus === 'heal_failed') ? `
      <div style="margin-top:12px;padding:10px 12px;background:rgba(220,53,69,0.1);border:1px solid var(--danger);border-radius:6px;font-size:12px;color:var(--danger);">
        ✗ 최대 힐링 횟수 초과 — 수동으로 실패 테스트를 수정하세요.
      </div>` : '';
    resultHtml = `
      <div class="exec-result-card">
        <div class="exec-result-header">
          <span class="exec-result-title">실행 결과</span>
          <span class="exec-result-badge ${badgeCls}">${badgeTxt}</span>
        </div>
        <div class="exec-result-stats">
          <div class="exec-stat"><div class="exec-stat-num" style="color:var(--text)">${execResult.total}</div><div class="exec-stat-label">Total</div></div>
          <div class="exec-stat"><div class="exec-stat-num" style="color:var(--approved-color)">${execResult.passed}</div><div class="exec-stat-label">Passed</div></div>
          <div class="exec-stat"><div class="exec-stat-num" style="color:var(--revision-color)">${execResult.failed}</div><div class="exec-stat-label">Failed</div></div>
          ${(execResult.skipped || 0) > 0 ? `<div class="exec-stat"><div class="exec-stat-num" style="color:#a855f7">${execResult.skipped}</div><div class="exec-stat-label">Skipped</div></div>` : ''}
          <div class="exec-stat"><div class="exec-stat-num" style="color:${allPass ? 'var(--approved-color)' : 'var(--revision-color)'}">${execResult.pass_rate}%</div><div class="exec-stat-label">Pass Rate</div></div>
        </div>
        ${groupResultsHtml}
        ${healBannerHtml}
        <div style="margin-top:12px;font-size:11px;color:var(--text-dim);">
          실행: ${esc(execResult.executed_at || '')} | 힐링: ${execResult.heal_count || 0}회
          ${execResult.report_name ? ` | <a href="#" onclick="event.preventDefault();showQuickReport('${esc(execResult.report_name)}')" style="color:var(--senior-accent);text-decoration:none;">리포트 보기</a>` : ''}
        </div>
      </div>`;
  }

  const logVis = _quickRunState.logVisible;
  main.innerHTML = `
    <div class="pipeline-view">
      <div class="pipeline-title">빠른 실행</div>
      <p style="font-size:12px;color:var(--text-dim);margin-bottom:16px;">
        tests/generated/ 에 이미 생성된 테스트 코드를 바로 실행합니다. 전체 파이프라인을 거치지 않습니다.
      </p>
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px;margin-bottom:16px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
          <span style="font-size:13px;font-weight:600;">테스트 폴더 선택</span>
          <label style="font-size:12px;color:var(--text-dim);cursor:pointer;display:flex;align-items:center;gap:4px;">
            <input type="checkbox" id="quick-select-all" onchange="quickToggleAll(this.checked)" checked>
            전체 선택
          </label>
        </div>
        <div class="quick-group-list">${groupsHtml}</div>
        <div style="display:flex;gap:10px;align-items:center;margin-top:14px;">
          <button class="action-btn action-btn-primary" id="quick-run-btn" onclick="runQuickTest()" ${!groups.length ? 'disabled' : ''}>
            ${_quickRunState.running ? '실행 중...' : '테스트 실행'}
          </button>
          <label style="font-size:12px;color:var(--text-dim);cursor:pointer;display:flex;align-items:center;gap:4px;">
            <input type="checkbox" id="quick-no-heal"> 힐링 생략
          </label>
          ${!groups.length ? '<span style="font-size:11px;color:var(--danger);">tests/generated/ 에 생성된 테스트가 없습니다</span>' : ''}
        </div>
      </div>
      <div class="run-log-box" id="run-quick-log" style="display:${logVis ? 'block' : 'none'};margin-bottom:16px;">
        <pre id="run-quick-log-content" style="margin:0;">${esc(_quickRunState.logContent || '(대기 중...)')}</pre>
      </div>
      <button class="log-toggle-btn" id="log-toggle-quick" onclick="toggleLogExpand('run-quick-log')" style="display:${logVis ? 'inline-block' : 'none'};margin-bottom:16px;">확대</button>
      ${resultHtml}
      <div class="quick-report-wrap" id="quick-report-wrap" style="display:${_uiState.quickReportName ? 'block' : 'none'};margin-top:16px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
          <span style="font-size:12px;color:var(--text-dim);">📄 리포트 미리보기</span>
          <button style="font-size:11px;background:transparent;border:1px solid var(--border);border-radius:6px;color:var(--text-dim);padding:2px 10px;cursor:pointer;" onclick="_uiState.quickReportName=null;this.closest('.quick-report-wrap').style.display='none';document.getElementById('quick-report-iframe').src='';">닫기</button>
        </div>
        <iframe id="quick-report-iframe"${_uiState.quickReportName ? ` src="/reports/${esc(_uiState.quickReportName)}"` : ''} style="width:100%;height:600px;border:1px solid var(--border);border-radius:var(--radius);background:#fff;"></iframe>
      </div>
      <div style="display:flex;justify-content:flex-end;margin-top:16px;">
        <button class="action-btn action-btn-danger" onclick="quickReset()">빠른 실행 초기화</button>
      </div>
    </div>`;

  // 체크 상태 복원 후 전체선택 체크박스 상태 동기화
  const allCb = document.getElementById('quick-select-all');
  const cbs = document.querySelectorAll('.quick-group-cb');
  if (allCb && cbs.length) {
    allCb.checked = Array.from(cbs).every(cb => cb.checked);
  }

  // 로그 스크롤 위치 복원 (맨 아래에 있었으면 자동 스크롤, 위로 올렸으면 위치 유지)
  const _newLogArea = document.getElementById('run-quick-log');
  if (_newLogArea && _logScrollTop !== null) {
    if (_wasAtBottom) {
      _newLogArea.scrollTop = _newLogArea.scrollHeight;
    } else {
      _newLogArea.scrollTop = _logScrollTop;
    }
  }

  // 실행 중이면 즉시 로그 갱신 (탭 전환 후 복귀 시 빈 화면 방지)
  if (_quickRunState.running && _quickRunState.logVisible) {
    fetch('/api/run_log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ log: 'quick_run.txt' }),
    }).then(r => r.json()).then(data => {
      const el = document.getElementById('run-quick-log-content');
      const area = document.getElementById('run-quick-log');
      if (el) el.textContent = data.log || '(대기 중...)';
      if (area) area.scrollTop = area.scrollHeight;
    }).catch(() => {});
  }
}

function quickToggleAll(checked) {
  document.querySelectorAll('.quick-group-cb').forEach(cb => { cb.checked = checked; });
}

async function runQuickTest() {
  const cbs = document.querySelectorAll('.quick-group-cb:checked');
  const groups = Array.from(cbs).map(cb => cb.value);
  if (!groups.length) { showToast('실행할 폴더를 선택하세요', 'info'); return; }

  const btn = document.getElementById('quick-run-btn');
  _quickRunState.running = true;
  _quickRunState.logContent = '';
  // 이전 실행 결과 클리어 (서버 + 클라이언트 모두)
  quickState = {};
  try { await fetch('/api/quick/reset', { method: 'POST' }); } catch (e) {}
  if (btn) { btn.textContent = '실행 중...'; btn.disabled = true; }
  // 결과 카드 즉시 제거
  const oldResult = document.querySelector('.exec-result-card');
  if (oldResult) oldResult.remove();

  try {
    const res = await fetch('/api/run_quick', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ groups, no_heal: !!document.getElementById('quick-no-heal')?.checked }),
    });
    const data = await res.json();
    if (data.ok) {
      _quickRunState.pid = data.pid;
      if (btn) btn.textContent = '실행됨 (PID: ' + (data.pid || '?') + ')';
      _quickRunState.logVisible = true;
      startLogPolling('run-quick-log', 'run-quick-log-content', 'quick_run.txt');
      // 완료 대기 → 결과 자동 갱신
      const checkDone = setInterval(async () => {
        await fetchQuickState();
        const qs = quickState || {};
        if (qs.status === 'done' || qs.status === 'heal_needed' || qs.status === 'heal_failed') {
          clearInterval(checkDone);
          _quickRunState._checkDoneTimer = null;
          // 로그 폴링 정리 + 최종 로그 보존
          if (_logTimers['run-quick-log']) {
            clearInterval(_logTimers['run-quick-log']);
            delete _logTimers['run-quick-log'];
          }
          const logEl = document.getElementById('run-quick-log-content');
          if (logEl) _quickRunState.logContent = logEl.textContent;
          _quickRunState.running = false;
          _quickRunState.pid = null;
          if (currentView === 'quick_run' && !_confirmOpen) renderQuickRun(document.getElementById('main'));
          if (btn) { btn.textContent = '테스트 실행'; btn.disabled = false; }
          if (qs.status === 'heal_needed') {
            const fc = qs.execution_result?.failed || 0;
            showHookAlert('quick_heal', `실패 ${fc}건 — 힐링 대기 중`);
          }
        }
      }, 3000);
      _quickRunState._checkDoneTimer = checkDone;
      // 최대 5분 후 자동 해제
      setTimeout(() => {
        clearInterval(checkDone);
        _quickRunState.running = false;
        _quickRunState.pid = null;
        _quickRunState._checkDoneTimer = null;
        if (btn) { btn.textContent = '테스트 실행'; btn.disabled = false; }
      }, 300000);
    } else {
      showToast('오류: ' + (data.error || 'unknown'));
      _quickRunState.running = false;
      if (btn) { btn.textContent = '테스트 실행'; btn.disabled = false; }
    }
  } catch (e) {
    showToast('서버 연결 오류');
    _quickRunState.running = false;
    if (btn) { btn.textContent = '테스트 실행'; btn.disabled = false; }
  }
}

function showQuickReport(name) {
  const wrap = document.getElementById('quick-report-wrap');
  const iframe = document.getElementById('quick-report-iframe');
  if (wrap && iframe) {
    if (name) {
      _uiState.quickReportName = name;
      wrap.style.display = 'block';
      iframe.src = '/reports/' + name;
      wrap.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      _uiState.quickReportName = null;
      wrap.style.display = 'none';
      iframe.src = '';
    }
  }
}

async function quickReset() {
  if (!(await safeConfirm('빠른 실행 상태를 초기화하시겠습니까?'))) return;
  // 타이머 정리
  if (_quickRunState._checkDoneTimer) {
    clearInterval(_quickRunState._checkDoneTimer);
  }
  if (_logTimers['run-quick-log']) {
    clearInterval(_logTimers['run-quick-log']);
    delete _logTimers['run-quick-log'];
  }
  const pidToKill = _quickRunState.pid;
  try {
    const res = await fetch('/api/quick/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pid: pidToKill }),
    });
    const data = await res.json();
    if (data.ok) {
      _quickRunState = { running: false, logVisible: false, logContent: '', pid: null, _checkDoneTimer: null };
      showToast('빠른 실행 초기화 완료', 'success');
      await refreshAll();
    } else {
      showToast('초기화 실패: ' + (data.error || ''));
    }
  } catch (e) { showToast('서버 연결 오류'); }
}
