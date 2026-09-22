// ── Failure Detail: 실패 TC 펼침 콘텐츠 (파이프라인 화면) ──
// GET /api/testcase/failure_detail 응답을 받아 스크린샷·기대결과/실패원인·
// 콘솔로그·네트워크실패·trace/영상 액션을 렌더링한다.

function _failNetStatusCls(status) {
  if (!status) return 's0';
  return status >= 400 ? 's4' : 's0';
}

function _failConsoleSection(consoleErrors) {
  const items = consoleErrors || [];
  const body = items.length
    ? items.map((log) => {
        const type = log.type === 'warning' ? 'warning' : 'error';
        const label = type === 'warning' ? 'WARN' : 'ERROR';
        return `<div class="fail-log-row">
          <span class="fail-log-dot ${type}"></span>
          <div class="fail-log-text"><span class="fail-log-tag ${type}">${label}</span>${esc(log.text || '')}</div>
        </div>`;
      }).join('')
    : '<div class="fail-card-empty">콘솔 에러 없음</div>';
  return `<div class="fail-card">
    <div class="fail-card-head"><span class="fd-dot" style="background:#f87171"></span>콘솔 로그${items.length ? `<span class="fd-count">${items.length}건</span>` : ''}</div>
    ${body}
  </div>`;
}

function _failNetworkSection(networkFailures) {
  const items = networkFailures || [];
  const body = items.length
    ? items.map((n) => {
        const cls = _failNetStatusCls(n.status);
        // status가 있으면 failure는 항상 "HTTP {status}"라 같은 정보를 중복
        // 표시하게 된다 — status 없이 failure만 있을 때만(net::ERR_FAILED 등
        // requestfailed 이벤트) 별도 사유 줄을 보여준다.
        const showReason = n.failure && !n.status;
        return `<div class="fail-net-row ${cls === 's4' ? 'bad' : ''}">
          <span class="fail-net-method">${esc(n.method || '')}</span>
          <span class="fail-net-status ${cls}">${n.status || '—'}</span>
          <span class="fail-net-req" title="${esc(n.url || '')}">${esc(n.url || '')}</span>
          ${showReason ? `<span class="fail-net-reason">${esc(n.failure)}</span>` : ''}
        </div>`;
      }).join('')
    : '<div class="fail-card-empty">실패한 네트워크 요청 없음</div>';
  return `<div class="fail-card">
    <div class="fail-card-head"><span class="fd-dot" style="background:#fbbf24"></span>네트워크${items.length ? `<span class="fd-count">${items.length}건</span>` : ''}</div>
    ${body}
  </div>`;
}

function _failActionsSection(data) {
  if (!data.trace_cmd && !data.video_url) return '';
  const parts = [];
  if (data.trace_cmd) {
    // 경로에 공백이 없어 브라우저가 줄바꿈할 자연스러운 지점이 없다 —
    // "/" 뒤에 <wbr>(줄바꿈 가능 지점)을 심어 폴더 경계에서만 끊기게 한다
    // (안 그러면 "traces" 같은 단어 중간에서 끊기는 문제가 있었다).
    const cmdWithBreaks = esc(data.trace_cmd).replace(/\//g, '/<wbr>');
    parts.push(`<span class="fd-cmd">${cmdWithBreaks}</span>`);
  }
  const buttons = [];
  if (data.video_url) {
    buttons.push(`<button class="fail-btn" onclick="window.open('${esc(data.video_url)}','_blank')">▶ 영상 재생</button>`);
  }
  if (data.trace_cmd) {
    // JSON.stringify는 큰따옴표로 감싸는데 onclick 속성 자체도 큰따옴표라
    // 속성이 중간에 끊어지는 버그가 있었다 — 작은따옴표로 감싸고 esc()로
    // HTML 이스케이프한다 (trace_cmd는 고정 형식 명령어라 따옴표를 포함하지 않는다).
    buttons.push(`<button class="fail-btn" onclick="navigator.clipboard && navigator.clipboard.writeText('${esc(data.trace_cmd)}')">복사</button>`);
  }
  return `<div class="fail-card">
    <div class="fail-actions">
      ${parts.join('')}
      <div class="fd-btn-row">${buttons.join('')}</div>
    </div>
  </div>`;
}

function renderFailureDetail(data) {
  const facts = [];
  if (data.group) facts.push(['그룹', data.group]);
  if (data.url) facts.push(['URL', data.url]);
  if (data.timestamp) facts.push(['실행 시각', data.timestamp]);

  const shot = data.screenshot_url
    ? `<img class="fail-shot" src="${esc(data.screenshot_url)}" alt="실패 시점 스크린샷" onclick="window.open('${esc(data.screenshot_url)}','_blank')">`
    : '';

  // 스텝은 "비교 대상"이 아니라 순서가 있는 절차라서 Expected/실패원인의
  // 초록/빨강 diff 박스가 아니라 번호 매긴 목록으로 별도 카드에 둔다.
  const stepLines = (data.steps || '').split('\n').map((s) => s.trim()).filter(Boolean);
  const stepsCard = stepLines.length
    ? `<div class="fail-card">
        <div class="fail-card-head"><span class="fd-dot" style="background:var(--text-dim)"></span>테스트 스텝</div>
        <div class="fail-card-body">
          <ol class="fail-steps">${stepLines.map((s) => `<li>${esc(s)}</li>`).join('')}</ol>
        </div>
      </div>`
    : '';

  const diffRows = [];
  if (data.expected) {
    diffRows.push(`<div class="fail-diff-row">
      <span class="fail-diff-label expect">Expected</span>
      <div class="fail-diff-value expect">${esc(data.expected)}</div>
    </div>`);
  }
  if (data.error_summary) {
    diffRows.push(`<div class="fail-diff-row">
      <span class="fail-diff-label actual">실패 원인</span>
      <div class="fail-diff-value actual mono">${esc(data.error_summary)}</div>
    </div>`);
  }

  const leftCards = [];
  if (shot) leftCards.push(`<div class="fail-card">${shot}</div>`);
  if (stepsCard) leftCards.push(stepsCard);
  if (diffRows.length) leftCards.push(`<div class="fail-card"><div class="fail-card-body">${diffRows.join('')}</div></div>`);
  if (facts.length) {
    leftCards.push(`<div class="fail-card">
      <div class="fail-card-head"><span class="fd-dot" style="background:var(--text-dim)"></span>요약 정보</div>
      <div class="fail-card-body fail-facts">
        ${facts.map(([k, v]) => `<div class="ff-row"><span class="ff-k">${esc(k)}</span><span class="ff-v">${esc(v)}</span></div>`).join('')}
      </div>
    </div>`);
  }

  const rightCards = [
    _failConsoleSection(data.console_errors),
    _failNetworkSection(data.network_failures),
    _failActionsSection(data),
  ].filter(Boolean);

  // auto-fit 그리드는 masonry가 아니라서, 카드 개수가 열 수로 딱 안
  // 나눠떨어지면(예: 7개 ÷ 4열 = 4+3) 마지막 줄 남는 칸이 빈 채로 남는다
  // (실제로 콘솔/네트워크 줄 오른쪽에 빈 공간으로 나타났다). flex 2단은
  // 두 칼럼이 항상 grow로 폭 100%를 나눠 갖기 때문에 구조적으로 빈
  // 공간이 생기지 않는다 — 대신 각 칼럼 안에서는 카드를 세로로 쌓는다.
  return `<div class="fail-detail">
    <div class="fail-detail-grid">
      <div class="fail-col">${leftCards.join('')}</div>
      <div class="fail-col">${rightCards.join('')}</div>
    </div>
  </div>`;
}
