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
  let html = '<div class="group-result-list">';
  grNames.forEach(g => {
    const gd = gr[g];
    const gPass = gd.failed === 0;
    const gSkipped = gd.skipped || 0;
    const gCls = gPass ? 'pass' : 'fail';
    const gBadge = gPass ? (gSkipped > 0 ? `PASS (${gSkipped} skip)` : 'PASS') : (gSkipped > 0 ? `FAIL (${gSkipped} skip)` : 'FAIL');
    const key = prefix + '__' + g;
    const isOpen = !!_groupOpenState[key];
    const testListHtml = buildTestListHtml(gd.tests || [], prefix, g);
    html += `
      <div class="group-result-item">
        <button type="button" class="group-result-header" onclick="toggleGroupResult('${esc(prefix)}','${esc(g)}')" aria-expanded="${isOpen}">
          <span class="group-result-chevron ${isOpen ? 'open' : ''}" id="grchv_${esc(prefix)}_${esc(g)}" aria-hidden="true">&#9654;</span>
          <span class="group-result-dot ${gCls}"></span>
          <span class="group-result-name">${esc(g.replace(/_/g, ' ').toUpperCase())}</span>
          <span class="group-result-count">${gd.passed}/${gd.passed + gd.failed} passed${gSkipped > 0 ? ` <span style="color:#a855f7;font-size:10px;">· ${gSkipped} skip</span>` : ''}</span>
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
