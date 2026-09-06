// ── Reports View ──
function reportSetSearch(value) {
  _reportListState.search = value;
  _reportListState.page = 1;
  _renderReportsOnly(true);
}

function reportSetPage(page) {
  _reportListState.page = page;
  _renderReportsOnly();
}

function reportFilteredItems() {
  const query = _reportListState.search.toLowerCase();
  return reportsList.filter(report => report.name.toLowerCase().includes(query)).sort((a, b) => {
    if (_reportListState.sort === 'name') return a.name.localeCompare(b.name);
    const difference = new Date(b.modified_at) - new Date(a.modified_at);
    return (_reportListState.sort === 'oldest' ? -difference : difference) || a.name.localeCompare(b.name);
  });
}

function _renderReportsOnly(focusSearch = false) {
  const main = document.getElementById('main');
  if (!main || currentView !== 'reports') return;
  const input = document.getElementById('report-search-input');
  const position = input ? input.selectionStart : null;
  const active = document.activeElement;
  const action = active?.dataset.action;
  const rowName = active?.closest('.report-item')?.dataset.name;
  const activeId = active?.id;
  const pageLabel = active?.closest('.report-pager') ? active.getAttribute('aria-label') : null;
  renderReports(main);
  if (focusSearch) {
    const next = document.getElementById('report-search-input');
    next.focus();
    if (position !== null) next.setSelectionRange(position, position);
  } else if (action && rowName) {
    [...main.querySelectorAll('.report-item')].find(row => row.dataset.name === rowName)?.querySelector(`[data-action="${action}"]`)?.focus();
  } else if (activeId === 'report-close') {
    main.querySelector('.report-item.is-open [data-action="open"]')?.focus();
    if (document.activeElement === document.body) document.getElementById('report-search-input').focus();
  } else if (pageLabel) {
    const button = [...main.querySelectorAll('.report-pager button')].find(item => item.getAttribute('aria-label') === pageLabel && !item.disabled);
    (button || main.querySelector('.report-pager button:not(:disabled)'))?.focus();
  } else if (activeId) {
    document.getElementById(activeId)?.focus();
  }
}

function renderReports(main) {
  const state = _reportListState;
  const names = new Set(reportsList.map(report => report.name));
  state.selected.forEach(name => { if (!names.has(name)) state.selected.delete(name); });
  if (!names.has(_uiState.openReportName)) _uiState.openReportName = null;
  const filtered = reportFilteredItems();
  const totalPages = Math.max(1, Math.ceil(filtered.length / REPORTS_PER_PAGE));
  state.page = Math.max(1, Math.min(state.page, totalPages));
  const pageItems = filtered.slice((state.page - 1) * REPORTS_PER_PAGE, state.page * REPORTS_PER_PAGE);
  const reportOpen = _uiState.openReportName;
  const oldFrame = document.getElementById('report-iframe');
  const previewUrl = reportOpen ? '/reports/' + encodeURIComponent(reportOpen) : '';
  const disabled = state.busy ? 'disabled' : '';
  main.innerHTML = `
    <div class="pipeline-view reports-view">
      <div class="pipeline-title">테스트 리포트</div>
      <p class="report-subtitle">생성된 실행 결과를 확인하고 필요한 리포트만 관리하세요.</p>
      <div class="report-controls">
        <input class="report-search" id="report-search-input" type="text" placeholder="리포트 이름 검색" aria-label="리포트 검색" value="${esc(state.search)}">
        <select id="report-sort" aria-label="리포트 정렬"><option value="newest">최신순</option><option value="oldest">오래된순</option><option value="name">파일명순</option></select>
        <button type="button" id="report-refresh" ${disabled}>새로고침</button>
        <button type="button" id="report-delete-selected" class="report-danger" ${state.busy || !state.selected.size ? 'disabled' : ''}>선택 삭제</button>
        <span class="report-count">${filtered.length}개 리포트${state.search ? ` / 전체 ${reportsList.length}개` : ''}</span>
      </div>
      <section class="report-workspace" aria-label="리포트 작업 공간" aria-busy="${state.busy}">
        <section class="report-panel" aria-label="리포트 목록">
          <div class="report-panel-head"><label class="report-select-all"><input type="checkbox" id="report-select-all" aria-label="검색 결과 전체 선택" ${!filtered.length || state.busy ? 'disabled' : ''}>전체 선택</label>
            <span class="report-selection-count" aria-live="polite">${state.selected.size}개 선택</span></div>
          <div class="report-list">${pageItems.map(report => `
            <div class="report-item ${report.name === reportOpen ? 'is-open' : ''}" data-name="${esc(report.name)}" role="group" aria-label="${esc(report.name)}">
              <input type="checkbox" aria-label="${esc(report.name)} 선택" ${state.selected.has(report.name) ? 'checked' : ''} ${disabled}>
              <div class="report-info"><div class="report-name" title="${esc(report.name)}">${esc(report.name)}</div>
                <div class="report-meta">${fmtDate(report.modified_at)} · ${Math.round(report.size / 1024)} KB</div></div>
              <div class="report-actions"><button type="button" data-action="open" aria-label="${esc(report.name)} 열기" aria-pressed="${report.name === reportOpen}">열기</button>
                <a href="/reports/${esc(encodeURIComponent(report.name))}" aria-label="${esc(report.name)} 새 탭" target="_blank" rel="noopener noreferrer">새 탭</a>
                <button type="button" data-action="delete" aria-label="${esc(report.name)} 삭제" class="report-danger" ${disabled}>삭제</button></div>
            </div>`).join('') || `<div class="report-empty">${reportsList.length ? '검색 결과가 없습니다.' : '리포트 없음 — 테스트 실행 후 리포트가 여기에 표시됩니다.'}</div>`}</div>
          <div class="report-pager"><button type="button" data-page="${state.page - 1}" aria-label="이전 페이지" ${state.page <= 1 ? 'disabled' : ''}>이전</button>
            <span>${state.page} / ${totalPages}</span><button type="button" data-page="${state.page + 1}" aria-label="다음 페이지" ${state.page >= totalPages ? 'disabled' : ''}>다음</button></div>
        </section>
        <section class="report-panel report-preview" aria-label="리포트 미리보기">
          <div class="report-panel-head"><strong class="report-preview-title">${reportOpen ? esc(reportOpen) : '미리보기'}</strong>${reportOpen ? '<button type="button" id="report-close">닫기</button>' : ''}</div>
          <div class="report-iframe-wrap" id="report-iframe-wrap" style="display:${reportOpen ? 'block' : 'none'}"></div>
          ${reportOpen ? '' : '<div class="report-empty report-preview-empty">왼쪽에서 리포트를 열어 확인하세요.</div>'}
        </section>
      </section>
    </div>`;
  if (reportOpen) {
    const frame = oldFrame && oldFrame.getAttribute('src') === previewUrl ? oldFrame : document.createElement('iframe');
    frame.id = 'report-iframe';
    frame.title = reportOpen + ' 리포트 미리보기';
    if (frame.getAttribute('src') !== previewUrl) frame.src = previewUrl;
    document.getElementById('report-iframe-wrap').appendChild(frame);
  }
  const search = document.getElementById('report-search-input');
  search.oninput = event => { if (!event.isComposing) reportSetSearch(event.target.value); };
  search.oncompositionend = event => reportSetSearch(event.target.value);
  const sort = document.getElementById('report-sort');
  sort.value = state.sort;
  sort.onchange = () => { state.sort = sort.value; state.page = 1; _renderReportsOnly(); document.getElementById('report-sort').focus(); };
  document.getElementById('report-refresh').onclick = reportRefresh;
  document.getElementById('report-delete-selected').onclick = () => reportDelete([...state.selected]);
  const selectAll = document.getElementById('report-select-all');
  const selectedCount = filtered.filter(report => state.selected.has(report.name)).length;
  selectAll.checked = !!filtered.length && selectedCount === filtered.length;
  selectAll.indeterminate = selectedCount > 0 && selectedCount < filtered.length;
  selectAll.onchange = () => {
    filtered.forEach(report => selectAll.checked ? state.selected.add(report.name) : state.selected.delete(report.name));
    _renderReportsOnly();
    document.getElementById('report-select-all').focus();
  };
  main.querySelectorAll('.report-item').forEach(row => {
    const name = row.dataset.name;
    row.querySelector('input').onchange = event => {
      event.target.checked ? state.selected.add(name) : state.selected.delete(name);
      _renderReportsOnly();
      [...main.querySelectorAll('.report-item')].find(item => item.dataset.name === name)?.querySelector('input').focus();
    };
    row.querySelector('[data-action="open"]').onclick = () => openReport(name);
    row.querySelector('[data-action="delete"]').onclick = () => reportDelete([name]);
  });
  main.querySelectorAll('[data-page]').forEach(button => { button.onclick = () => reportSetPage(Number(button.dataset.page)); });
  const close = document.getElementById('report-close');
  if (close) close.onclick = closeReport;
}

function openReport(name) { _uiState.openReportName = name; _renderReportsOnly(); }
function closeReport() {
  const name = _uiState.openReportName;
  _uiState.openReportName = null;
  _renderReportsOnly();
  [...document.querySelectorAll('.report-item')].find(row => row.dataset.name === name)?.querySelector('[data-action="open"]').focus();
}

async function reportRefresh() {
  if (_reportListState.busy) return;
  _reportListState.busy = true;
  _renderReportsOnly();
  const success = await fetchReports();
  _reportListState.busy = false;
  _renderReportsOnly();
  showToast(success ? '리포트 목록을 새로고침했습니다.' : '리포트 목록을 불러오지 못했습니다.', success ? 'success' : 'error');
}

function reportConfirmDelete(names) {
  return new Promise(resolve => {
    _confirmOpen = true;
    const previousFocus = document.activeElement;
    const dialog = document.createElement('dialog');
    dialog.className = 'report-delete-dialog';
    dialog.setAttribute('aria-labelledby', 'report-delete-title');
    dialog.setAttribute('aria-describedby', 'report-delete-description');
    dialog.innerHTML = `<form method="dialog"><h2 id="report-delete-title">리포트 삭제</h2>
      <p id="report-delete-description">${names.length === 1 ? esc(names[0]) : `${names.length}개 리포트`}를 삭제하시겠습니까?<br>삭제한 리포트는 복구할 수 없습니다.</p>
      <div class="report-dialog-actions"><button value="cancel" autofocus>취소</button><button value="delete" class="report-danger">삭제</button></div></form>`;
    dialog.addEventListener('close', () => {
      _confirmOpen = false;
      const confirmed = dialog.returnValue === 'delete';
      dialog.remove();
      if (previousFocus?.isConnected) previousFocus.focus();
      resolve(confirmed);
    }, { once: true });
    document.body.appendChild(dialog);
    dialog.showModal();
  });
}

async function reportDelete(names) {
  if (_reportListState.busy || _confirmOpen || !names.length) return;
  if (!(await reportConfirmDelete(names))) return;
  _reportListState.busy = true;
  ++_reportFetchVersion;
  _renderReportsOnly();
  try {
    const response = await fetch('/api/reports/delete', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ names }),
    });
    const raw = await response.text();
    let result;
    try { result = raw ? JSON.parse(raw) : {}; } catch { result = {}; }
    if (!response.ok) throw new Error(result.error || `리포트 삭제 요청이 거부되었습니다. (${response.status})`);
    const removed = new Set([...result.deleted, ...result.missing]);
    reportsList = reportsList.filter(report => !removed.has(report.name));
    removed.forEach(name => _reportListState.selected.delete(name));
    if (removed.has(_uiState.openReportName)) _uiState.openReportName = null;
    const refreshed = await fetchReports();
    const failed = result.failed || [];
    showToast(`${result.deleted.length}개 리포트를 삭제했습니다.${result.missing.length ? ` 이미 없는 리포트 ${result.missing.length}개.` : ''}${failed.length ? ` ${failed.length}개 삭제 실패: ${failed.map(item => item.name).join(', ')}` : ''}`, failed.length ? 'error' : 'success');
    if (!refreshed) showToast('삭제는 완료했지만 목록 새로고침에 실패했습니다.');
  } catch (error) {
    showToast(error.message || '리포트 삭제에 실패했습니다.');
  } finally {
    _reportListState.busy = false;
    _renderReportsOnly();
  }
}
