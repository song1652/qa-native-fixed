// TC 스튜디오 — 엑셀 가져오기 모달 (PRD F2.1~F2.4, F2.6, F6.7)
(function (NS) {
  'use strict';

  const { state, api, esc, $, $$, toast } = NS;
  let root = null;
  let preview = null;

  NS.importModal = { html, mount, open };

  function html() {
    return `
  <div class="scrim" id="import-modal" data-id="import-modal" hidden>
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="im-title">
      <div class="panel-head"><span id="im-title">엑셀을 라이브러리로 가져오기</span><span class="spacer"></span>
        <button class="icon-btn" data-id="import-close" id="import-close" aria-label="닫기">✕</button></div>
      <div class="panel-body" style="display:grid;gap:12px">
        <label class="drop" id="import-drop" data-id="import-pick-file" for="import-file">
          <b>엑셀 파일을 끌어다 놓거나 눌러서 선택</b>
          <span class="faint">.xlsx · 최대 25MB · 헤더 행은 자동으로 찾습니다 · 원본 파일은 수정하지 않습니다</span>
        </label>
        <input type="file" id="import-file" data-id="import-file-input" accept=".xlsx" hidden>
        <div id="import-preview" hidden style="display:grid;gap:12px">
          <div class="field"><span class="label">스위트 이름</span>
            <input class="input" id="import-suite" data-id="import-suite" placeholder="예: 야핏무브" autocomplete="off">
            <span class="help">같은 이름이 있으면 case_id가 같은 케이스를 갱신하고, 없는 케이스는 추가합니다.</span></div>
          <div class="field"><span class="label">가져올 시트 · case_id 접두어</span>
            <div class="radio-list" id="import-sheets" data-id="import-sheets"></div></div>
          <ul class="checks" id="import-warnings" data-id="import-warnings"></ul>
        </div>
        <div class="row"><span class="help" id="import-summary"></span><span class="spacer"></span>
          <button class="btn btn-ghost" data-id="import-cancel" id="import-cancel">취소</button>
          <button class="btn btn-primary" data-id="import-confirm" id="import-confirm" disabled>가져오기</button></div>
      </div>
    </div>
  </div>`;
  }

  function open() {
    preview = null;
    $('#import-preview', root).hidden = true;
    $('#import-confirm', root).disabled = true;
    $('#import-summary', root).textContent = '';
    $('#import-file', root).value = '';
    $('#import-modal', root).hidden = false;
  }

  const closeModal = () => { $('#import-modal', root).hidden = true; };

  async function pick(file) {
    if (!file) return;
    if (!/\.xlsx$/i.test(file.name)) { toast(`${esc(file.name)}: .xlsx 파일만 가져올 수 있습니다.`, 'err'); return; }
    if (file.size > 25 * 1024 * 1024) { toast(`${esc(file.name)}: 25MB를 넘습니다.`, 'err'); return; }
    $('#import-summary', root).textContent = '분석 중…';
    try {
      preview = await api.importPreview(file);
    } catch (err) {
      $('#import-summary', root).textContent = '';
      toast(`엑셀을 분석하지 못했습니다: ${esc(err.message)}`, 'err');
      return;
    }
    $('#import-suite', root).value = state.suite || file.name.replace(/\.xlsx$/i, '').replace(/_?Full$/i, '').replace(/[^\w가-힣-]/g, '_');
    $('#import-sheets', root).innerHTML = preview.sheets.map((s, i) => `
      <label class="radio"><input type="checkbox" data-sheet="${esc(s.name)}" checked> ${esc(s.name)}
        <span class="n">${s.cases}행 · 헤더 ${s.header_row}행</span>
        <input class="input mono" data-prefix="${esc(s.name)}" value="S${String(i + 1).padStart(2, '0')}" maxlength="8" style="width:90px" aria-label="${esc(s.name)} 접두어"></label>`).join('');
    const warnings = preview.sheets.flatMap((s) => s.warnings.map((w) => `${s.name}: ${w}`));
    $('#import-warnings', root).innerHTML = warnings.map((w) => `<li><span class="wr">!</span>${esc(w)}</li>`).join('')
      + '<li><span class="faint">·</span> 결과 컬럼(And·iOS)은 실행 결과로 가져옵니다. 두 값이 다르면 Fail > N/A > Pass > NT 순으로 합칩니다</li>';
    $('#import-preview', root).hidden = false;
    updateSummary();
  }

  function selection() {
    const sheets = $$('#import-sheets input[type=checkbox]', root).filter((c) => c.checked).map((c) => c.dataset.sheet);
    const prefixes = {};
    $$('#import-sheets input[data-prefix]', root).forEach((i) => { prefixes[i.dataset.prefix] = i.value.trim().toUpperCase(); });
    return { sheets, prefixes };
  }

  function updateSummary() {
    if (!preview) return;
    const { sheets, prefixes } = selection();
    const count = preview.sheets.filter((s) => sheets.includes(s.name)).reduce((n, s) => n + s.cases, 0);
    const badPrefix = sheets.some((s) => !/^[A-Z][A-Z0-9]{0,7}$/.test(prefixes[s]));
    const suite = $('#import-suite', root).value.trim();
    $('#import-summary', root).textContent = badPrefix ? '접두어는 영문 대문자로 시작하는 8자 이내여야 합니다' : `${count}건 · ${sheets.length}시트`;
    $('#import-confirm', root).disabled = !sheets.length || badPrefix || !/^[\w가-힣-]+$/.test(suite) || suite.startsWith('_');
    $('#import-confirm', root).textContent = `${count}건 가져오기`;
  }

  async function confirm() {
    const btn = $('#import-confirm', root);
    btn.classList.add('loading');
    btn.disabled = true;
    try {
      const suite = $('#import-suite', root).value.trim();
      const res = await api.importCommit({ preview_id: preview.preview_id, suite, ...selection() });
      closeModal();
      toast(`가져왔습니다 · 추가 ${res.created} · 갱신 ${res.updated} · 그대로 ${res.unchanged}`, 'ok');
      await NS.reloadSuites(suite);
    } catch (err) {
      toast(`가져오지 못했습니다: ${esc(err.message)}`, 'err');
      btn.disabled = false;
    } finally {
      btn.classList.remove('loading');
    }
  }

  function mount(r) {
    root = r;
    const drop = $('#import-drop', root);
    ['dragover', 'dragenter'].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add('over'); }));
    ['dragleave', 'drop'].forEach((ev) => drop.addEventListener(ev, () => drop.classList.remove('over')));
    drop.addEventListener('drop', (e) => { e.preventDefault(); pick(e.dataTransfer.files[0]); });
    $('#import-file', root).addEventListener('change', (e) => pick(e.target.files[0]));
    $('#import-sheets', root).addEventListener('input', updateSummary);
    $('#import-suite', root).addEventListener('input', updateSummary);
    ['#import-close', '#import-cancel'].forEach((s) => $(s, root).addEventListener('click', closeModal));
    $('#import-confirm', root).addEventListener('click', confirm);
  }
})(window.TCS_NS = window.TCS_NS || {});
