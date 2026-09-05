// ── Reports View ──
function reportSetSearch(val) {
  _reportListState.search = val.toLowerCase();
  _reportListState.page = 1;
  _renderReportsOnly();
}

function reportSetPage(p) {
  _reportListState.page = p;
  _renderReportsOnly();
}

function _renderReportsOnly() {
  const main = document.getElementById('main');
  if (main && currentView === 'reports') {
    renderReports(main);
    const inp = document.getElementById('report-search-input');
    if (inp) { inp.focus(); inp.setSelectionRange(inp.value.length, inp.value.length); }
  }
}

function renderReports(main) {
  if (!reportsList.length) {
    main.innerHTML = `
      <div class="pipeline-view">
        <div class="pipeline-title">테스트 리포트</div>
        <div class="empty"><div class="empty-icon">&#x1F4CA;</div><h2>리포트 없음</h2><p>테스트 실행 후 리포트가 여기에 표시됩니다</p></div>
      </div>`;
    return;
  }

  const q = _reportListState.search;
  const filtered = q ? reportsList.filter(r => r.name.toLowerCase().includes(q)) : reportsList;
  const totalPages = Math.max(1, Math.ceil(filtered.length / REPORTS_PER_PAGE));
  const page = Math.min(_reportListState.page, totalPages);
  const start = (page - 1) * REPORTS_PER_PAGE;
  const pageItems = filtered.slice(start, start + REPORTS_PER_PAGE);

  let controlsHtml = `<div class="report-controls">`;
  controlsHtml += `<input class="report-search" id="report-search-input" type="text" placeholder="리포트 검색…" aria-label="리포트 검색" value="${esc(q)}" oninput="reportSetSearch(this.value)">`;
  controlsHtml += `<span class="report-count">${filtered.length}개`;
  if (q) controlsHtml += ` / 전체 ${reportsList.length}개`;
  controlsHtml += `</span>`;
  if (totalPages > 1) {
    controlsHtml += `<div class="report-pager">`;
    controlsHtml += `<button onclick="reportSetPage(${page - 1})" ${page <= 1 ? 'disabled' : ''}>&laquo;</button>`;
    controlsHtml += `<span>${page} / ${totalPages}</span>`;
    controlsHtml += `<button onclick="reportSetPage(${page + 1})" ${page >= totalPages ? 'disabled' : ''}>&raquo;</button>`;
    controlsHtml += `</div>`;
  }
  controlsHtml += `</div>`;

  let listHtml = '';
  pageItems.forEach(r => {
    const sizeKb = Math.round(r.size / 1024);
    listHtml += `
      <button type="button" class="report-item" onclick="openReport('${esc(r.name)}')" aria-label="${esc(r.name)} 리포트 열기">
        <span class="report-icon" aria-hidden="true">&#x1F4C4;</span>
        <div class="report-info">
          <div class="report-name">${esc(r.name)}</div>
          <div class="report-meta">${fmtDate(r.modified_at)} &middot; ${sizeKb}KB</div>
        </div>
        <button type="button" class="report-open-btn" onclick="event.stopPropagation();window.open('/reports/${esc(r.name)}','_blank')">새 탭</button>
      </button>`;
  });

  const reportOpen = _uiState.openReportName;
  main.innerHTML = `
    <div class="pipeline-view">
      <div class="pipeline-title">테스트 리포트</div>
      ${controlsHtml}
      <div class="report-list">${listHtml}</div>
      <div class="report-iframe-wrap" id="report-iframe-wrap" style="display:${reportOpen ? 'block' : 'none'}">
        <div style="display:flex;justify-content:flex-end;padding:6px 8px;background:var(--surface);border-bottom:1px solid var(--border);">
          <button style="font-size:11px;background:transparent;border:1px solid var(--border);border-radius:6px;color:var(--text-dim);padding:2px 10px;cursor:pointer;" onclick="closeReport()">닫기</button>
        </div>
        <iframe id="report-iframe"${reportOpen ? ` src="/reports/${esc(reportOpen)}"` : ''}></iframe>
      </div>
    </div>`;
}

function openReport(name) {
  _uiState.openReportName = name;
  const wrap = document.getElementById('report-iframe-wrap');
  const iframe = document.getElementById('report-iframe');
  if (wrap && iframe) {
    iframe.src = '/reports/' + name;
    wrap.style.display = 'block';
    wrap.scrollIntoView({ behavior: 'smooth' });
  }
}

function closeReport() {
  _uiState.openReportName = null;
  const wrap = document.getElementById('report-iframe-wrap');
  const iframe = document.getElementById('report-iframe');
  if (wrap) wrap.style.display = 'none';
  if (iframe) iframe.src = '';
}
