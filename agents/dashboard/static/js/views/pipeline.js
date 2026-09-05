// ── Single Pipeline View ──
function buildRunPanel(mode) {
  const groups = pagesData.groups || [];
  if (mode === 'single') {
    const pages = pagesData.pages || {};
    let pageOpts = '<option value="">-- 페이지 선택 --</option>';
    for (const [name, entry] of Object.entries(pages)) {
      const url = typeof entry === 'string' ? entry : (entry && entry.url) || '';
      const spa = (typeof entry === 'object' && entry.spa) ? ' (SPA)' : '';
      pageOpts += `<option value="${esc(name)}" data-url="${esc(url)}">${esc(name)}${spa}</option>`;
    }
    let caseOpts = '<option value="">-- 케이스 폴더 선택 --</option>';
    groups.forEach(g => {
      caseOpts += `<option value="${esc(g.name)}">${esc(g.name)} (${g.count}개 케이스)</option>`;
    });
    return `
      <div class="run-pipeline-form">
        <h3>run_qa.py 실행</h3>
        <div class="run-form-row">
          <label class="run-form-label" for="run-page-select">페이지</label>
          <select class="run-form-select" id="run-page-select" onchange="onPageSelect()">${pageOpts}</select>
        </div>
        <div class="run-form-row">
          <span class="run-form-label">URL</span>
          <div class="run-form-url-display" id="run-url-display">페이지를 선택하세요</div>
        </div>
        <div class="run-form-row">
          <label class="run-form-label" for="run-case-select">케이스</label>
          <select class="run-form-select" id="run-case-select">${caseOpts}</select>
        </div>
        <div class="run-form-actions">
          <button class="action-btn action-btn-primary" id="run-single-btn" onclick="runSingleQA()" ${!groups.length ? 'disabled title="testcases/ 폴더에 케이스가 없습니다"' : ''}>run_qa.py 실행</button>
          ${!groups.length ? '<span style="font-size:11px;color:var(--danger);margin-left:8px;">testcases/ 폴더에 케이스 파일이 없습니다</span>' : ''}
        </div>
        <div style="display:flex;align-items:center;margin-top:8px;">
          <div class="run-log-box" id="run-single-log" style="flex:1;margin-top:0;"><pre id="run-single-log-content" style="margin:0;"></pre></div>
        </div>
        <button class="log-toggle-btn" id="log-toggle-single" onclick="toggleLogExpand('run-single-log')" style="display:none;margin-top:4px;">확대</button>
      </div>`;
  } else {
    return `
      <div class="run-pipeline-form">
        <h3>run_qa_parallel.py 실행</h3>
        <div class="run-form-row">
          <span class="run-form-label">대상</span>
          <span style="font-size:12px;color:var(--text-dim);">config/pages.json + testcases/ 자동 스캔 → subagent 병렬 코드 생성</span>
        </div>
        <div class="run-form-actions">
          <button class="action-btn action-btn-primary" id="run-parallel-btn" onclick="runParallelQA()" ${!groups.length ? 'disabled title="testcases/ 폴더에 케이스가 없습니다"' : ''}>run_qa_parallel.py 실행</button>
          ${!groups.length ? '<span style="font-size:11px;color:var(--danger);margin-left:8px;">testcases/ 폴더에 케이스 파일이 없습니다</span>' : ''}
        </div>
        <div style="display:flex;align-items:center;margin-top:8px;">
          <div class="run-log-box" id="run-parallel-log" style="flex:1;margin-top:0;"><pre id="run-parallel-log-content" style="margin:0;"></pre></div>
        </div>
        <button class="log-toggle-btn" id="log-toggle-parallel" onclick="toggleLogExpand('run-parallel-log')" style="display:none;margin-top:4px;">확대</button>
      </div>`;
  }
}

function onPageSelect() {
  const sel = document.getElementById('run-page-select');
  const urlDisp = document.getElementById('run-url-display');
  const caseSel = document.getElementById('run-case-select');
  if (!sel) return;
  const opt = sel.options[sel.selectedIndex];
  const url = opt ? opt.getAttribute('data-url') : '';
  const pageName = sel.value;
  if (urlDisp) urlDisp.textContent = url || '페이지를 선택하세요';
  if (urlDisp) urlDisp.style.color = url ? 'var(--text)' : 'var(--text-dim)';
  // 같은 이름의 케이스 폴더 자동 선택
  if (caseSel && pageName) {
    for (let i = 0; i < caseSel.options.length; i++) {
      if (caseSel.options[i].value === pageName) { caseSel.selectedIndex = i; break; }
    }
  }
}

// 단일 파이프라인 실행
async function runSingleQA() {
  const pageSel = document.getElementById('run-page-select');
  const caseSel = document.getElementById('run-case-select');
  const btn = document.getElementById('run-single-btn');
  if (!pageSel || !caseSel) return;
  const opt = pageSel.options[pageSel.selectedIndex];
  const url = opt ? opt.getAttribute('data-url') : '';
  const casesDir = caseSel.value;
  if (!url || !casesDir) { showToast('페이지와 케이스 폴더를 선택하세요', 'info'); return; }
  if (btn) { btn.textContent = '실행 중…'; btn.disabled = true; }
  try {
    const res = await fetch('/api/run_qa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, cases_dir: casesDir }),
    });
    const data = await res.json();
    if (data.ok) {
      if (btn) btn.textContent = '실행됨 (PID: ' + (data.pid || '?') + ')';
      startLogPolling('run-single-log', 'run-single-log-content', 'run_qa.txt');
      waitForSingleInit(url);
      setTimeout(() => { if (btn) { btn.textContent = 'run_qa.py 실행'; btn.disabled = false; } }, 60000);
    } else {
      showToast('오류: ' + (data.error || 'unknown'));
      if (btn) { btn.textContent = 'run_qa.py 실행'; btn.disabled = false; }
    }
  } catch (e) {
    showToast('서버 연결 오류');
    if (btn) { btn.textContent = 'run_qa.py 실행'; btn.disabled = false; }
  }
}

// state/pipeline.json step=init + url 있으면 알림
function waitForSingleInit(url) {
  let elapsed = 0;
  const check = setInterval(async () => {
    elapsed += 2;
    if (elapsed > 60) { clearInterval(check); return; }
    try {
      const res = await fetch('/api/pipeline_state');
      const data = await res.json();
      if (data.step === 'init' && data.url) {
        clearInterval(check);
        showHookAlert('single_init', url + ' 파이프라인 초기화 완료');
      }
    } catch (e) { }
  }, 2000);
}

function renderSinglePipeline(main) {
  // 선택값 보존 (5초 폴링으로 DOM 교체 시 리셋 방지)
  const prevPage = (document.getElementById('run-page-select') || {}).value || '';
  const prevCase = (document.getElementById('run-case-select') || {}).value || '';
  // 로그 스크롤 위치 보존
  const _sLogArea = document.getElementById('run-single-log');
  const _sLogScrollTop = _sLogArea ? _sLogArea.scrollTop : null;
  const _sWasAtBottom = _sLogScrollTop === null || (_sLogArea.scrollHeight - _sLogScrollTop - _sLogArea.clientHeight < 40);

  const state = pipelineState || {};
  const currentStep = state.step || 'init';
  // heal_needed/heal_failed는 reviewed 이후 단계이므로 done 위치(5)에 active로 표시
  const isHeal = currentStep === 'heal_needed' || currentStep === 'heal_failed';
  // STEP_COMPAT은 constants.js 전역 변수 — /api/pipeline_registry fetch 후 갱신 (P45)
  let stepIdx = isHeal ? 5 : PIPELINE_STEPS.indexOf(currentStep);
  if (stepIdx === -1) stepIdx = PIPELINE_STEPS.indexOf(STEP_COMPAT[currentStep] || 'init');

  let stepsHtml = '';
  PIPELINE_STEPS.forEach((step, i) => {
    let cls = '';
    if (i < stepIdx) cls = 'done';
    else if (i === stepIdx) cls = 'active';
    // heal 상태에서 done(마지막) 위치는 힐링 색상
    if (isHeal && i === 5) cls = 'active';
    const labelCls = cls;
    const num = i + 1;
    const label = (isHeal && i === 5) ? STEP_LABELS[currentStep] : STEP_LABELS[step];
    stepsHtml += `<div class="step-node"><div class="step-circle ${cls}">${i < stepIdx ? '&#10003;' : num}</div><div class="step-label ${labelCls}">${label}</div></div>`;
    if (i < PIPELINE_STEPS.length - 1) {
      stepsHtml += `<div class="step-line ${i < stepIdx ? 'done' : ''}"></div>`;
    }
  });

  const url = state.url || '-';
  const healCount = state.heal_count || 0;
  const execResult = state.execution_result || {};

  let actionsHtml = '';

  const resetBtnHtml = `<div class="pipeline-actions" style="margin-top:16px;"><button class="action-btn action-btn-danger" onclick="pipelineReset()" style="margin-left:auto;">파이프라인 초기화</button></div>`;

  let infoRows = `
    <div class="pipeline-info-row"><span class="pipeline-info-label">URL</span><span class="pipeline-info-val">${esc(url)}</span></div>
    <div class="pipeline-info-row"><span class="pipeline-info-label">현재 단계</span><span class="pipeline-info-val">${STEP_LABELS[currentStep] || currentStep}</span></div>
    <div class="pipeline-info-row"><span class="pipeline-info-label">힐링 횟수</span><span class="pipeline-info-val">${healCount}</span></div>`;

  // 승인/반려 단계 제거됨 — 심의 완료 후 자동 실행
  // 실행 결과 카드 (병렬 파이프라인과 동일 구조)
  let singleExecResultHtml = '';
  if (execResult.total !== undefined && execResult.total > 0) {
    const allPass = execResult.failed === 0;
    const badgeCls = allPass ? 'pass' : 'fail';
    const badgeTxt = allPass ? 'ALL PASS' : `${execResult.failed} FAILED`;

    const groupResultsHtml = buildGroupResultsHtml(execResult.group_results || {}, 'single');

    singleExecResultHtml = `
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
          ${execResult.report_name ? ` | <a href="#" onclick="event.preventDefault();showSingleReport('${esc(execResult.report_name)}')" style="color:var(--senior-accent);text-decoration:none;">리포트 보기</a>` : ''}
        </div>
      </div>
      <div class="single-report-wrap" id="single-report-wrap" style="display:${_uiState.singleReportName ? 'block' : 'none'};">
        <div style="display:flex;justify-content:flex-end;padding:6px 8px;background:var(--surface);border-bottom:1px solid var(--border);">
          <button style="font-size:11px;background:transparent;border:1px solid var(--border);border-radius:6px;color:var(--text-dim);padding:2px 10px;cursor:pointer;" onclick="_uiState.singleReportName=null;this.closest('.single-report-wrap').style.display='none';document.getElementById('single-report-iframe').src='';">닫기</button>
        </div>
        <iframe id="single-report-iframe"${_uiState.singleReportName ? ` src="/reports/${esc(_uiState.singleReportName)}"` : ''}></iframe>
      </div>`;
  }

  main.innerHTML = `
    <div class="pipeline-view">
      <div class="pipeline-title">단일 파이프라인</div>
      <div class="step-progress">${stepsHtml}</div>
      <div class="pipeline-info">${infoRows}</div>
      ${actionsHtml}
      ${singleExecResultHtml}
      ${resetBtnHtml}
    </div>`;

  // 상태 없으면 실행 패널 + 안내 표시
  if (!state.step) {
    main.innerHTML = `
      <div class="pipeline-view">
        <div class="pipeline-title">단일 파이프라인</div>
        ${buildRunPanel('single')}
        <div class="empty"><div class="empty-icon">&#x1F50D;</div><h2>파이프라인 비활성</h2><p>위에서 URL과 케이스를 선택해 실행하거나, 터미널에서 run_qa.py를 실행하세요</p></div>
      </div>`;
  } else {
    // 이미 실행 중이어도 상단에 실행 패널 추가
    const view = main.querySelector('.pipeline-view');
    if (view) {
      const titleEl = view.querySelector('.pipeline-title');
      if (titleEl) titleEl.insertAdjacentHTML('afterend', buildRunPanel('single'));
    }
  }

  // 선택값 복원
  const pageSel = document.getElementById('run-page-select');
  const caseSel = document.getElementById('run-case-select');
  if (pageSel && prevPage) { pageSel.value = prevPage; onPageSelect(); }
  if (caseSel && prevCase) caseSel.value = prevCase;

  // 로그 스크롤 복원
  const _sNewLog = document.getElementById('run-single-log');
  if (_sNewLog && _sLogScrollTop !== null) {
    _sNewLog.scrollTop = _sWasAtBottom ? _sNewLog.scrollHeight : _sLogScrollTop;
  }
}

async function pipelineReset() {
  if (!(await safeConfirm('파이프라인 상태를 초기화하시겠습니까?'))) return;
  try {
    const res = await fetch('/api/pipeline/reset', { method: 'POST' });
    const data = await res.json();
    if (data.ok) { showToast('파이프라인 초기화 완료', 'success'); await refreshAll(); }
    else showToast('초기화 실패: ' + (data.error || ''));
  } catch (e) { showToast('서버 연결 오류'); }
}

function showSingleReport(name) {
  const wrap = document.getElementById('single-report-wrap');
  const iframe = document.getElementById('single-report-iframe');
  if (wrap && iframe) {
    if (wrap.style.display === 'none') {
      _uiState.singleReportName = name;
      iframe.src = '/reports/' + name;
      wrap.style.display = 'block';
      wrap.scrollIntoView({ behavior: 'smooth' });
    } else {
      _uiState.singleReportName = null;
      wrap.style.display = 'none';
      iframe.src = '';
    }
  }
}
