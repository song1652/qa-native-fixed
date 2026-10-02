// ── Group Result: 접기/펼치기 공통 ──
function toggleGroupResult(prefix, groupName) {
  const key = prefix + '__' + groupName;
  _groupOpenState[key] = !_groupOpenState[key];
  const body = document.getElementById('grb_' + prefix + '_' + groupName);
  const chv = document.getElementById('grchv_' + prefix + '_' + groupName);
  if (body) body.style.display = _groupOpenState[key] ? 'block' : 'none';
  if (chv) chv.classList.toggle('open', !!_groupOpenState[key]);
}

function buildGroupResultsHtml(gr, prefix) {
  const grNames = Object.keys(gr).sort();
  if (!grNames.length) return '';
  let html = '<div class="group-result-list"><div class="group-result-columns"><span>그룹</span><span>통과</span><span>결과</span></div>';
  grNames.forEach(g => {
    const gd = gr[g];
    const gPass = gd.failed === 0;
    const gSkipped = gd.skipped || 0;
    const gCls = gPass ? 'pass' : 'fail';
    const gBadge = gPass ? (gSkipped > 0 ? `통과 (건너뜀 ${gSkipped})` : '통과') : (gSkipped > 0 ? `실패 (건너뜀 ${gSkipped})` : '실패');
    const key = prefix + '__' + g;
    const isOpen = !!_groupOpenState[key];
    const testListHtml = buildTestListHtml(gd.tests || [], prefix, g);
    html += `
      <div class="group-result-item">
        <button type="button" class="group-result-header" onclick="toggleGroupResult('${esc(prefix)}','${esc(g)}')" aria-expanded="${isOpen}">
          <span class="group-result-chevron ${isOpen ? 'open' : ''}" id="grchv_${esc(prefix)}_${esc(g)}" aria-hidden="true">&#9654;</span>
          <span class="group-result-dot ${gCls}"></span>
          <span class="group-result-name">${esc(g)}</span>
          <span class="group-result-count">${gd.passed}/${gd.passed + gd.failed}${gSkipped > 0 ? ` <span style="color:var(--warn);font-size:12px;">· 건너뜀 ${gSkipped}</span>` : ''}</span>
          <span class="group-result-badge ${gCls}">${gBadge}</span>
        </button>
        <div class="group-result-body" id="grb_${esc(prefix)}_${esc(g)}" style="display:${isOpen ? 'block' : 'none'}">
          ${testListHtml}
        </div>
      </div>`;
  });
  html += '</div>';
  return html;
}
