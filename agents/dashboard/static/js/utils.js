// ── Utility Functions ──
function esc(s) {
  return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function fmtTime(iso) {
  if (!iso) return '';
  try { return new Date(iso).toLocaleTimeString('ko-KR', { hour12: false }); } catch { return ''; }
}

function fmtDate(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('ko-KR') + ' ' + d.toLocaleTimeString('ko-KR', { hour12: false });
  } catch { return ''; }
}

function showToast(msg, type = 'error') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = 'toast toast-' + type;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => { if (el.parentNode) el.remove(); }, 3600);
}

function toggleLogExpand(logAreaId) {
  const area = document.getElementById(logAreaId);
  if (!area) return;
  area.classList.toggle('expanded');
  const btn = area.parentElement.querySelector('.log-toggle-btn');
  if (btn) btn.textContent = area.classList.contains('expanded') ? '축소' : '확대';
}

function showHookAlert(type, detail) {
  if (type === 'single_init' || type === 'parallel') {
    showToast(`${detail} · 자동 실행 중입니다. 진행 상태에서 결과를 확인하세요.`, 'info');
    return;
  }
  const existing = document.getElementById('hook-alert');
  if (existing) existing.remove();

  const configs = {
    discuss: {
      title: '토론이 예약되었습니다',
      desc: `<strong style="color:var(--accent);">"${esc(detail)}"</strong>`,
      action: 'Claude Code에서 <strong>아무 메시지</strong>를 보내주세요.<br>훅이 자동으로 토론을 시작합니다.'
    },
    single_approved: {
      title: '파이프라인 승인 완료',
      desc: `<strong style="color:var(--accent);">${detail}</strong>`,
      action: 'Claude Code에서 <strong>아무 메시지</strong>를 보내주세요.<br>훅이 자동으로 테스트를 실행합니다.'
    },
    discuss_approved: {
      title: '팀 토론 승인 완료',
      desc: `<strong style="color:var(--accent);">${detail}</strong>`,
      action: 'Claude Code에서 <strong>아무 메시지</strong>를 보내주세요.<br>훅이 승인된 항목을 자동으로 구현합니다.'
    },
    quick_heal: {
      title: '힐링이 필요합니다',
      desc: `<strong style="color:var(--fail);">${detail}</strong>`,
      action: 'Claude Code에서 <strong>아무 메시지</strong>를 보내주세요.<br>훅이 자동으로 힐링을 시작합니다.'
    }
  };
  const cfg = configs[type] || configs.discuss;

  const overlay = document.createElement('div');
  overlay.id = 'hook-alert';
  overlay.className = 'dashboard-confirm-scrim';

  const box = document.createElement('div');
  box.className = 'dashboard-confirm-dialog';
  box.innerHTML = `
    <h2 class="dashboard-confirm-head" style="margin:0;">${cfg.title}</h2>
    <div class="dashboard-confirm-body">
      <p style="margin:0 0 12px;">${cfg.desc}</p>
      <p style="margin:0;color:var(--text-2);">${cfg.action}</p>
    </div>
    <div class="dashboard-confirm-actions">
      <button class="action-btn action-btn-primary" onclick="this.closest('#hook-alert').remove()">확인</button>
    </div>
  `;
  overlay.appendChild(box);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
}

// 로그 폴링 (3초 간격, 최대 1800초)
function startLogPolling(logAreaId, logContentId, logFileName, runId) {
  if (_logTimers[logAreaId]) clearInterval(_logTimers[logAreaId]);
  const area = document.getElementById(logAreaId);
  if (area) area.style.display = 'block';
  // 토글 버튼 표시
  const toggleIdMap = {
    'run-single-log': 'log-toggle-single',
    'run-parallel-log': 'log-toggle-parallel',
    'run-quick-log': 'log-toggle-quick',
  };
  const toggleBtn = document.getElementById(toggleIdMap[logAreaId] || '');
  if (toggleBtn) toggleBtn.style.display = 'inline-block';
  let elapsed = 0;
  let _firstPoll = true;
  const poll = async () => {
    try {
      const res = await fetch('/api/run_log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ log: logFileName, ...(runId ? {run_id: runId} : {}) }),
      });
      const data = await res.json();
      const el = document.getElementById(logContentId);
      const logArea = document.getElementById(logAreaId);
      if (el && logArea) {
        // 현재 스크롤 위치 저장 (업데이트 전)
        const prevScrollTop = logArea.scrollTop;
        const isAtBottom = _firstPoll || (logArea.scrollHeight - prevScrollTop - logArea.clientHeight < 40);
        const logText = data.log || '(대기 중…)';
        el.textContent = logText;
        // 맨 아래에 있었으면 자동 스크롤, 위로 올렸으면 위치 유지
        if (isAtBottom) {
          logArea.scrollTop = logArea.scrollHeight;
        } else {
          logArea.scrollTop = prevScrollTop;
        }
        _firstPoll = false;
        // 빠른 실행: 재렌더링 시 내용 보존을 위해 상태에 저장
        if (logAreaId === 'run-quick-log' && data.log) {
          _quickRunState.logContent = data.log;
        }
      }
    } catch (e) { }
    elapsed += 3;
    if (elapsed >= 1800 && _logTimers[logAreaId]) {
      clearInterval(_logTimers[logAreaId]);
      delete _logTimers[logAreaId];
    }
  };
  poll();
  _logTimers[logAreaId] = setInterval(poll, 3000);
}

function executionFailed(state, result) {
  return ['failed', 'error', 'cancelled', 'interrupted', 'timed_out', 'incomplete'].includes(state.workflow_status)
    || ['failed', 'cancelled', 'interrupted', 'timed_out', 'incomplete'].includes((result || {}).status);
}

function recoveryGuidanceHtml(state, result) {
  result = result || {};
  if (!executionFailed(state, result) && !result.recovery_stopped && !result.recovery_stop) return '';
  const recovery = result.recovery_stop || result.recovery || {};
  return `<div class="pipeline-heal-notice failed"><strong>${esc(recovery.title || '실행 확인 필요')}</strong><p>${esc(recovery.message || state.error || result.error || '실행 로그에서 중단 원인을 확인하세요.')}</p>${!result.report_name ? '<p>리포트 없음 · 실행 기록과 로그는 보존됩니다.</p>' : ''}</div>`;
}
