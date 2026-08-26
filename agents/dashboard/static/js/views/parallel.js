// ── Parallel Pipeline View ──
function buildParallelStepProgress(status, files, totalTargets) {
  // generating은 스크립트가 아닌 Claude Code가 수행 → 파일 생성 여부로 추론
  let effectiveStatus = status;
  if (status === 'ready' && files.length > 0 && files.length < totalTargets) {
    effectiveStatus = 'generating';
  } else if (status === 'ready' && totalTargets > 0 && files.length >= totalTargets) {
    effectiveStatus = 'generating';  // 완료 직전
  }

  const isHeal = effectiveStatus === 'heal_needed' || effectiveStatus === 'heal_failed';
  const stepIdx = isHeal ? PARALLEL_STEPS.length : PARALLEL_STEPS.indexOf(effectiveStatus);

  let html = '';
  PARALLEL_STEPS.forEach((step, i) => {
    let cls = '';
    if (stepIdx >= 0 && i < stepIdx) cls = 'done';
    else if (i === stepIdx) cls = 'active';
    if (isHeal && i === PARALLEL_STEPS.length - 1) cls = 'active';
    const labelCls = cls;
    const num = i + 1;
    const label = (isHeal && i === PARALLEL_STEPS.length - 1)
      ? PARALLEL_STEP_LABELS[effectiveStatus]
      : PARALLEL_STEP_LABELS[step];
    html += `<div class="step-node"><div class="step-circle ${cls}">${i < stepIdx ? '&#10003;' : num}</div><div class="step-label ${labelCls}">${label}</div></div>`;
    if (i < PARALLEL_STEPS.length - 1) {
      html += `<div class="step-line ${stepIdx >= 0 && i < stepIdx ? 'done' : ''}"></div>`;
    }
  });
  return `<div class="step-progress">${html}</div>`;
}

function renderParallelPipeline(main) {
  // 로그 스크롤 위치 보존
  const _pLogArea = document.getElementById('run-parallel-log');
  const _pLogScrollTop = _pLogArea ? _pLogArea.scrollTop : null;
  const _pWasAtBottom = _pLogScrollTop === null || (_pLogArea.scrollHeight - _pLogScrollTop - _pLogArea.clientHeight < 40);

  const batch = batchState || {};
  const ps = batch.parallel_state || {};
  const files = batch.generated_files || [];
  const status = ps.status || '';
  // total_cases = TC 파일 기준 (total_count는 그룹 수라 케이스 수와 다름)
  const totalTargets = ps.total_cases || ps.total_count || 0;
  const execResult = ps.execution_result || null;

  // step-progress 바
  const stepProgressHtml = status ? buildParallelStepProgress(status, files, totalTargets) : '';

  // 상태 정보 행
  let infoRows = '';
  if (status) {
    const displayStatus = PARALLEL_STEP_LABELS[status] || status;
    const healCount = (execResult && execResult.heal_count) || 0;
    infoRows = `<div class="pipeline-info" style="margin-bottom:16px;">
      <div class="pipeline-info-row"><span class="pipeline-info-label">상태</span><span class="pipeline-info-val">${esc(displayStatus)}</span></div>
      <div class="pipeline-info-row"><span class="pipeline-info-label">대상</span><span class="pipeline-info-val">${totalTargets}개 케이스</span></div>
      <div class="pipeline-info-row"><span class="pipeline-info-label">생성 파일</span><span class="pipeline-info-val">${files.length}개${totalTargets ? ' / ' + totalTargets + '개' : ''}</span></div>
      ${healCount ? `<div class="pipeline-info-row"><span class="pipeline-info-label">힐링 횟수</span><span class="pipeline-info-val">${healCount}</span></div>` : ''}
    </div>`;
  }

  // 그룹별 파일 묶기
  const groups = {};
  files.forEach(f => {
    if (!groups[f.group]) groups[f.group] = [];
    groups[f.group].push(f);
  });
  const groupNames = Object.keys(groups).sort();

  let filesHtml = '';
  if (groupNames.length) {
    filesHtml = `<table style="width:100%;border-collapse:collapse;font-size:12px;margin-top:12px;">
      <thead><tr style="color:var(--text-dim);text-align:left;border-bottom:1px solid var(--border);">
        <th style="padding:6px 12px;">그룹</th><th style="padding:6px 12px;text-align:right;">파일 수</th><th style="padding:6px 12px;text-align:right;">크기</th>
      </tr></thead><tbody>`;
    groupNames.forEach(g => {
      const gFiles = groups[g];
      const totalSize = gFiles.reduce((sum, f) => sum + f.size, 0);
      filesHtml += `<tr style="border-bottom:1px solid var(--border);">
        <td style="padding:6px 12px;color:var(--text);">${esc(g)}</td>
        <td style="padding:6px 12px;text-align:right;color:var(--text-dim);">${gFiles.length}개</td>
        <td style="padding:6px 12px;text-align:right;color:var(--text-dim);">${(totalSize / 1024).toFixed(1)} KB</td>
      </tr>`;
    });
    filesHtml += '</tbody></table>';
  }

  // summaryHtml은 infoRows로 대체됨 (step-progress 바 아래 표시)
  const summaryHtml = '';

  // 실행 결과 카드
  let execResultHtml = '';
  if (execResult) {
    const allPass = execResult.failed === 0;
    const badgeCls = allPass ? 'pass' : 'fail';
    const badgeTxt = allPass ? 'ALL PASS' : `${execResult.failed} FAILED`;

    const groupResultsHtml = buildGroupResultsHtml(execResult.group_results || {}, 'parallel');

    execResultHtml = `
      <div class="exec-result-card">
        <div class="exec-result-header">
          <span class="exec-result-title">테스트 실행 결과</span>
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
        <div style="margin-top:12px;font-size:11px;color:var(--text-dim);">
          실행: ${esc(execResult.executed_at || '')} | 힐링: ${execResult.heal_count || 0}회
          ${execResult.report_name ? ` | <a href="#" onclick="event.preventDefault();showParallelReport('${esc(execResult.report_name)}')" style="color:var(--senior-accent);text-decoration:none;">리포트 보기</a>` : ''}
        </div>
      </div>
      <div class="parallel-report-wrap" id="parallel-report-wrap" style="display:${_uiState.parallelReportName ? 'block' : 'none'};">
        <div style="display:flex;justify-content:flex-end;padding:6px 8px;background:var(--surface);border-bottom:1px solid var(--border);">
          <button style="font-size:11px;background:transparent;border:1px solid var(--border);border-radius:6px;color:var(--text-dim);padding:2px 10px;cursor:pointer;" onclick="_uiState.parallelReportName=null;this.closest('.parallel-report-wrap').style.display='none';document.getElementById('parallel-report-iframe').src='';">닫기</button>
        </div>
        <iframe id="parallel-report-iframe"${_uiState.parallelReportName ? ` src="/reports/${esc(_uiState.parallelReportName)}"` : ''}></iframe>
      </div>`;
  }

  const mlVisible = _uiState.mergeLogVisible;
  main.innerHTML = `
    <div class="pipeline-view">
      <div class="pipeline-title">병렬 파이프라인</div>
      ${stepProgressHtml}
      ${infoRows}
      ${buildRunPanel('parallel')}
      ${summaryHtml}
      ${execResultHtml}
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <button class="action-btn action-btn-danger" onclick="parallelReset()" style="margin-left:auto;">parallel_state 초기화</button>
      </div>
      <div id="merge-log-area" style="${mlVisible ? '' : 'display:none;'}margin-bottom:16px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px;max-height:400px;overflow-y:auto;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <span style="font-size:12px;font-weight:600;color:var(--text-dim);">MERGE LOG</span>
          <button style="font-size:11px;background:transparent;border:1px solid var(--border);border-radius:6px;color:var(--text-dim);padding:2px 8px;cursor:pointer;" onclick="_uiState.mergeLogVisible=false;document.getElementById('merge-log-area').style.display='none'">닫기</button>
        </div>
        <pre id="merge-log-content" style="font-size:11px;color:var(--text);white-space:pre-wrap;word-break:break-all;font-family:Consolas,monospace;margin:0;">${esc(_uiState.mergeLogContent)}</pre>
      </div>
      ${files.length ? `<div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px;">
        <div style="font-size:13px;font-weight:600;margin-bottom:8px;">tests/generated/ 파일 목록</div>
        ${filesHtml}
      </div>` : `<div class="empty"><div class="empty-icon">&#x2699;&#xFE0F;</div><h2>생성된 테스트 없음</h2><p>run_qa_parallel.py를 실행하고 subagent로 코드를 생성하세요</p></div>`}
    </div>`;

  // 로그 스크롤 복원
  const _pNewLog = document.getElementById('run-parallel-log');
  if (_pNewLog && _pLogScrollTop !== null) {
    _pNewLog.scrollTop = _pWasAtBottom ? _pNewLog.scrollHeight : _pLogScrollTop;
  }
}

// 병렬 파이프라인 실행
async function runParallelQA() {
  const btn = document.getElementById('run-parallel-btn');
  if (btn) { btn.textContent = '실행 중...'; btn.disabled = true; }
  try {
    const res = await fetch('/api/run_qa_parallel', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      if (btn) btn.textContent = '실행됨 (PID: ' + (data.pid || '?') + ')';
      startLogPolling('run-parallel-log', 'run-parallel-log-content', 'run_parallel.txt');
      // state/parallel.json이 ready가 되면 알림 표시
      waitForParallelReady();
      setTimeout(() => { if (btn) { btn.textContent = 'run_qa_parallel.py 실행'; btn.disabled = false; } }, 60000);
    } else {
      showToast('오류: ' + (data.error || 'unknown'));
      if (btn) { btn.textContent = 'run_qa_parallel.py 실행'; btn.disabled = false; }
    }
  } catch (e) {
    showToast('서버 연결 오류');
    if (btn) { btn.textContent = 'run_qa_parallel.py 실행'; btn.disabled = false; }
  }
}

// state/parallel.json status=ready 감지 → Claude Code 안내 알림
function waitForParallelReady() {
  let elapsed = 0;
  const check = setInterval(async () => {
    elapsed += 2;
    if (elapsed > 120) { clearInterval(check); return; }
    try {
      const res = await fetch('/api/batch_state');
      const data = await res.json();
      if (data.parallel_state && data.parallel_state.status === 'ready') {
        clearInterval(check);
        const count = data.parallel_state.total_cases || data.parallel_state.total_count || '?';
        showHookAlert('parallel', count + '개 테스트 대상이 준비되었습니다');
      }
    } catch (e) { }
  }, 2000);
}

function showParallelReport(name) {
  const wrap = document.getElementById('parallel-report-wrap');
  const iframe = document.getElementById('parallel-report-iframe');
  if (wrap && iframe) {
    if (wrap.style.display === 'none') {
      _uiState.parallelReportName = name;
      iframe.src = '/reports/' + name;
      wrap.style.display = 'block';
      wrap.scrollIntoView({ behavior: 'smooth' });
    } else {
      _uiState.parallelReportName = null;
      wrap.style.display = 'none';
      iframe.src = '';
    }
  }
}

async function runMerge() {
  const btn = document.getElementById('merge-btn');
  if (btn) { btn.textContent = '실행 중...'; btn.disabled = true; }
  try {
    const res = await fetch('/api/run_merge', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      if (btn) btn.textContent = '실행됨 (PID: ' + (data.pid || '?') + ')';
      _uiState.mergeLogVisible = true;
      const logBtn = document.getElementById('merge-log-btn');
      if (logBtn) logBtn.style.display = 'inline-block';
      // 3초 후 로그 자동 표시
      setTimeout(showMergeLog, 3000);
      // 30초 후 버튼 복원
      setTimeout(() => { if (btn) { btn.textContent = '99_merge.py 실행'; btn.disabled = false; } }, 30000);
    } else {
      showToast('오류: ' + (data.error || 'unknown'));
      if (btn) { btn.textContent = '99_merge.py 실행'; btn.disabled = false; }
    }
  } catch (e) {
    showToast('서버 연결 오류');
    if (btn) { btn.textContent = '99_merge.py 실행'; btn.disabled = false; }
  }
}

async function showMergeLog() {
  try {
    const res = await fetch('/api/merge_log', { method: 'POST' });
    const data = await res.json();
    _uiState.mergeLogVisible = true;
    _uiState.mergeLogContent = data.log || '(로그 없음)';
    const area = document.getElementById('merge-log-area');
    const content = document.getElementById('merge-log-content');
    if (area && content) {
      content.textContent = _uiState.mergeLogContent;
      area.style.display = 'block';
      area.scrollTop = area.scrollHeight;
    }
    const logBtn = document.getElementById('merge-log-btn');
    if (logBtn) logBtn.style.display = 'inline-block';
  } catch (e) { }
}

async function parallelReset() {
  if (!(await safeConfirm('병렬 파이프라인 상태를 초기화하시겠습니까?'))) return;
  try {
    const res = await fetch('/api/parallel/reset', { method: 'POST' });
    const data = await res.json();
    if (data.ok) {
      _uiState.parallelReportName = null;
      _uiState.mergeLogVisible = false;
      _uiState.mergeLogContent = '';
      showToast('병렬 파이프라인 초기화 완료', 'success');
      await refreshAll();
    } else {
      showToast('초기화 실패: ' + (data.error || ''));
    }
  } catch (e) { showToast('서버 연결 오류'); }
}
