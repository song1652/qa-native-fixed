// ── Test List: Filter + Pagination (공통) ──
function _getTestListKey(prefix, groupName) { return prefix + '__' + (groupName || 'all'); }

function _getState(key) {
  if (!_testListState[key]) _testListState[key] = { filter: 'all', page: 1 };
  return _testListState[key];
}

function testListSetFilter(prefix, groupName, filter) {
  const st = _getState(_getTestListKey(prefix, groupName));
  st.filter = filter;
  st.page = 1;
  refreshAll();
}

function testListSetPage(prefix, groupName, page) {
  const st = _getState(_getTestListKey(prefix, groupName));
  st.page = page;
  refreshAll();
}

// nodeid가 tc_*.py 파일을 포함하는지 여부만 체크 (서버가 매칭 처리)
function _hasTcFile(nodeid) {
  if (!nodeid) return false;
  const parts = nodeid.split('/');
  const pyFile = parts[parts.length - 1].split('::')[0];
  return /^tc_(?:[A-Za-z]+_)?\d+_/.test(pyFile);
}

async function toggleTestDetail(rowId, nodeid) {
  const detailRow = document.getElementById('td_' + rowId);
  if (!detailRow) return;

  // 이미 열려 있으면 닫기
  if (detailRow.style.display !== 'none') {
    detailRow.style.display = 'none';
    _testDetailOpen[nodeid] = false;
    return;
  }

  const contentCell = detailRow.querySelector('.tc-detail-content');
  if (!contentCell) return;

  // 캐시된 콘텐츠가 있으면 바로 표시
  if (_testDetailContent[nodeid]) {
    contentCell.textContent = _testDetailContent[nodeid];
    detailRow.style.display = '';
    _testDetailOpen[nodeid] = true;
    return;
  }

  // 로딩 표시 후 펼침
  contentCell.textContent = '불러오는 중...';
  detailRow.style.display = '';
  _testDetailOpen[nodeid] = true;

  if (!_hasTcFile(nodeid)) {
    const msg = '(테스트케이스 파일 경로를 확인할 수 없습니다)';
    contentCell.textContent = msg;
    _testDetailContent[nodeid] = msg;
    return;
  }

  try {
    const res = await fetch(`/api/testcase?nodeid=${encodeURIComponent(nodeid)}`);
    const data = await res.json();
    const text = data.ok ? data.content : `(${data.error || '파일 없음'})`;
    contentCell.textContent = text;
    _testDetailContent[nodeid] = text;
  } catch (e) {
    const msg = '(로드 실패)';
    contentCell.textContent = msg;
    _testDetailContent[nodeid] = msg;
  }
}

function buildTestListHtml(tests, prefix, groupName) {
  if (!tests || !tests.length) return '';
  const key = _getTestListKey(prefix, groupName);
  const st = _getState(key);
  const filter = st.filter;
  const _outcome = t => t.outcome || (t.passed ? 'passed' : 'failed');
  const filtered = filter === 'all' ? tests : tests.filter(t => {
    const oc = _outcome(t);
    if (filter === 'pass') return oc === 'passed';
    if (filter === 'skip') return oc === 'skipped';
    return oc === 'failed';
  });
  const totalPages = Math.max(1, Math.ceil(filtered.length / TESTS_PER_PAGE));
  const page = Math.min(st.page, totalPages);
  const start = (page - 1) * TESTS_PER_PAGE;
  const pageItems = filtered.slice(start, start + TESTS_PER_PAGE);
  const passCount = tests.filter(t => _outcome(t) === 'passed').length;
  const skipCount = tests.filter(t => _outcome(t) === 'skipped').length;
  const failCount = tests.filter(t => _outcome(t) === 'failed').length;

  const pfx = esc(prefix);
  const gn = esc(groupName || '');
  let html = '<div class="test-list-controls">';
  html += `<button class="test-filter-btn ${filter === 'all' ? 'active-all' : ''}" onclick="testListSetFilter('${pfx}','${gn}','all')">All (${tests.length})</button>`;
  html += `<button class="test-filter-btn ${filter === 'pass' ? 'active-pass' : ''}" onclick="testListSetFilter('${pfx}','${gn}','pass')">Pass (${passCount})</button>`;
  html += `<button class="test-filter-btn ${filter === 'fail' ? 'active-fail' : ''}" onclick="testListSetFilter('${pfx}','${gn}','fail')">Fail (${failCount})</button>`;
  if (skipCount > 0) html += `<button class="test-filter-btn ${filter === 'skip' ? 'active-skip' : ''}" onclick="testListSetFilter('${pfx}','${gn}','skip')">Skip (${skipCount})</button>`;
  if (totalPages > 1) {
    html += `<div class="test-list-pager">`;
    html += `<button onclick="testListSetPage('${pfx}','${gn}',${page - 1})" ${page <= 1 ? 'disabled' : ''}>&laquo;</button>`;
    html += `<span>${page} / ${totalPages}</span>`;
    html += `<button onclick="testListSetPage('${pfx}','${gn}',${page + 1})" ${page >= totalPages ? 'disabled' : ''}>&raquo;</button>`;
    html += `</div>`;
  }
  html += '</div>';

  html += '<table class="test-list-table"><thead><tr><th style="width:30px">#</th><th>테스트</th><th style="width:80px">상태</th></tr></thead><tbody>';
  pageItems.forEach((t, i) => {
    const num = start + i + 1;
    const oc = _outcome(t);
    const cls = oc === 'passed' ? 'pass' : oc === 'skipped' ? 'skip' : 'fail';
    const label = oc === 'passed' ? 'PASS' : oc === 'skipped' ? 'SKIP' : 'FAIL';
    const rawNodeid = t.nodeid || '';
    const rowId = esc(pfx) + '_' + esc(gn) + '_' + (start + i);
    const nodeid = esc(rawNodeid);
    const hasTc = _hasTcFile(rawNodeid);
    const isOpen = hasTc && !!_testDetailOpen[rawNodeid];
    const cachedContent = hasTc && _testDetailContent[rawNodeid] ? esc(_testDetailContent[rawNodeid]) : '';
    const displayName = t.title || t.name;
    const clickable = hasTc ? `style="cursor:pointer;" tabindex="0" role="button" aria-label="${esc(displayName)} 테스트케이스 보기" onclick="toggleTestDetail('${rowId}','${nodeid}')" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();toggleTestDetail('${rowId}','${nodeid}')}"` : '';
    html += `<tr ${clickable}><td style="color:var(--text-dim)">${num}</td><td>${esc(displayName)}${hasTc ? ' <span style="font-size:10px;opacity:0.4;" aria-hidden="true">▼</span>' : ''}</td><td style="white-space:nowrap"><span class="test-status-dot ${cls}"></span>${label}</td></tr>`;
    if (hasTc) {
      html += `<tr id="td_${rowId}" style="display:${isOpen ? '' : 'none'};"><td colspan="3" style="padding:0;"><pre class="tc-detail-content" style="margin:0;padding:10px 16px;font-size:11px;background:var(--surface);border-top:1px solid var(--border);color:var(--text-dim);white-space:pre-wrap;word-break:break-all;max-height:320px;overflow-y:auto;">${cachedContent}</pre></td></tr>`;
    }
  });
  html += '</tbody></table>';
  return html;
}
