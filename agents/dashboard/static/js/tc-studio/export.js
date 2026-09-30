// TC 스튜디오 — 내보내기 화면 (Phase 1: 엑셀 카드만. md 카드는 Phase 4) (PRD F6)
(function (NS) {
  'use strict';

  const { state, api, esc, $, $$, toast } = NS;
  let root = null;
  let lastExport = null;

  NS.exportView = { html, mount, onShow };

  function html() {
    return `
  <section class="screen" id="screen-export" data-screen="export">
    <div class="wrap">
      <div class="exp">
        <div class="panel exp-card" style="padding:16px">
          <div class="head"><div class="fmt xl">XLSX</div><div><b style="font-size:14px">엑셀로 내보내기</b>
            <div class="help">가져온 템플릿의 사본에 계층 순서대로 씁니다. 원본 파일은 바꾸지 않습니다.</div></div></div>
          <div class="field"><span class="label">범위</span>
            <div class="radio-list" data-id="xlsx-scope">
              <label class="radio"><input type="radio" name="xscope" value="all" checked> 전체 <span class="n" id="x-all-n"></span></label>
              <label class="radio"><input type="radio" name="xscope" value="sheets"> 선택한 시트
                <select class="fselect" id="xlsx-sheets" data-id="xlsx-sheets" multiple size="3" style="margin-left:6px"></select></label>
              <label class="radio"><input type="radio" name="xscope" value="case_ids"> 현재 필터 결과 <span class="n" id="x-filter-n"></span></label>
              <label class="radio"><input type="radio" name="xscope" value="approved"> 승인된 케이스만</label>
            </div></div>
          <div class="warnbox" data-id="xlsx-openpyxl-warning"><b>다시 저장하면 사라질 수 있는 요소</b>
            <span>이미지·차트와 일부 조건부서식은 사본에서 빠질 수 있습니다. 검사 결과를 확인한 뒤 내려받으세요.</span></div>
          <div class="field"><span class="label">무결성 검사</span>
            <ul class="checks" id="xlsx-checks" data-id="xlsx-integrity"><li class="faint">내보내기 전에 검사를 실행하세요</li></ul>
            <button class="btn btn-ghost" data-id="xlsx-run-check" id="xlsx-run-check" style="justify-self:start">검사 실행</button></div>
          <div class="field"><span class="label">History 시트에 추가할 행</span>
            <textarea class="textarea" id="xlsx-history-note" data-id="xlsx-history-note" rows="3"></textarea></div>
          <div class="field"><span class="label">파일 이름</span><div class="fname" id="xlsx-filename" data-id="xlsx-filename">—</div></div>
          <button class="btn btn-primary" data-id="xlsx-download" id="xlsx-download" disabled style="justify-self:start">검사 후 내려받기</button>
        </div>
      </div>
    </div>
  </section>`;
  }

  function onShow() {
    lastExport = null;
    const suite = state.suites.find((s) => s.suite === state.suite);
    $('#x-all-n', root).textContent = suite ? suite.count : 0;
    $('#x-filter-n', root).textContent = state.items.length;
    $('#xlsx-sheets', root).innerHTML = (suite ? suite.sheets : []).map((s) => `<option selected>${esc(s)}</option>`).join('');
    const d = new Date();
    const yymmdd = `${String(d.getFullYear()).slice(2)}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`;
    if (!$('#xlsx-history-note', root).value) $('#xlsx-history-note', root).value = `${yymmdd} TC 스튜디오 반영\n- `;
    resetCheck('');
  }

  function resetCheck(msg) {
    lastExport = null;
    $('#xlsx-download', root).disabled = true;
    $('#xlsx-download', root).textContent = '검사 후 내려받기';
    $('#xlsx-filename', root).textContent = '—';
    $('#xlsx-checks', root).innerHTML = `<li class="faint">${msg || '내보내기 전에 검사를 실행하세요'}</li>`;
  }

  function payload() {
    const scope = $('input[name="xscope"]:checked', root).value;
    const body = { scope, history_note: $('#xlsx-history-note', root).value.trim() };
    if (scope === 'sheets') body.sheets = $$('#xlsx-sheets option', root).filter((o) => o.selected).map((o) => o.value);
    if (scope === 'case_ids') body.case_ids = state.items.map((c) => c.case_id);
    return body;
  }

  async function runCheck(e) {
    const btn = e.currentTarget;
    btn.classList.add('loading');
    btn.disabled = true;
    $('#xlsx-checks', root).innerHTML = '<li class="faint">사본에 쓰고 다시 여는 중…</li>';
    try {
      lastExport = await api.exportXlsx(state.suite, payload());
      $('#xlsx-checks', root).innerHTML = lastExport.checks.map((c) =>
        `<li><span class="${c.level === 'ok' ? 'ok' : 'bad'}">${c.level === 'ok' ? '✓' : '✕'}</span>${esc(c.message)}</li>`).join('');
      $('#xlsx-filename', root).textContent = lastExport.filename;
      const ok = lastExport.checks.every((c) => c.level === 'ok');
      $('#xlsx-download', root).disabled = false;
      $('#xlsx-download', root).textContent = ok ? `내려받기 (${lastExport.count}건)` : '오류가 있지만 내려받기';
    } catch (err) {
      resetCheck(`검사 실패: ${esc(err.message)}`);
    } finally {
      btn.classList.remove('loading');
      btn.disabled = false;
    }
  }

  function mount(r) {
    root = r;
    $$('input[name="xscope"]', root).forEach((i) => i.addEventListener('change', () => resetCheck('범위가 바뀌었습니다. 검사를 다시 실행하세요')));
    $('#xlsx-sheets', root).addEventListener('change', () => resetCheck('범위가 바뀌었습니다. 검사를 다시 실행하세요'));
    $('#xlsx-run-check', root).addEventListener('click', runCheck);
    $('#xlsx-download', root).addEventListener('click', () => {
      if (!lastExport) return;
      const a = document.createElement('a');
      a.href = api.downloadUrl(lastExport.export_id);
      a.download = lastExport.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      toast(`${esc(lastExport.filename)} 파일을 내려받습니다.`, 'ok');
    });
  }
})(window.TCS_NS = window.TCS_NS || {});
