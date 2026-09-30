// TC 스튜디오 — 새로 생성: 소스 수집 · 대상 가지 · 작성 프로필 · 작업 진행 (목업 2번 화면, PRD F1·F3·F4)
// Phase 3는 registerSourceTab()으로 URL·Confluence·Figma 탭을 끼워 넣는다.
(function (NS) {
  'use strict';

  const { state, api, esc, $, $$, toast } = NS;
  const STEPS = [['queued', '대기'], ['fetching', '수집'], ['drafting', '초안 작성'], ['validating', '검증'], ['done', '완료']];
  const ICON = { file: 'PDF', paste: 'T', url: 'URL', conf: 'C', figma: 'F' };
  const tabs = [];            // {id, label, html(), mount(root, addSource)}
  let root = null;
  let bundle = { bundle_id: '', sources: [] };
  let profiles = [];
  let job = null;
  let poll = null;

  NS.generateView = { html, mount, onShow, registerSourceTab, prefill };

  function registerSourceTab(tab) { tabs.push(tab); }

  // ── Phase 2 기본 소스 탭: 파일 · 붙여넣기 ─────────────────────
  registerSourceTab({
    id: 'file', label: 'PRD 파일',
    html: () => `<label class="drop" id="src-file-drop" data-id="src-file-drop" for="src-file-input">
        <b>파일을 끌어다 놓거나 눌러서 선택</b><span class="faint">.pdf · .docx · .md · .txt · 최대 25MB · PDF 200쪽</span></label>
      <input type="file" id="src-file-input" data-id="src-file-input" accept=".pdf,.docx,.md,.txt" hidden>`,
    mount: (r, add) => {
      const drop = $('#src-file-drop', r);
      const pick = async (file) => {
        if (!file) return;
        if (!/\.(pdf|docx|md|txt)$/i.test(file.name)) { toast(`${esc(file.name)}: .pdf .docx .md .txt만 올릴 수 있습니다.`, 'err'); return; }
        if (file.size > 25 * 1024 * 1024) { toast(`${esc(file.name)}: 25MB를 넘습니다.`, 'err'); return; }
        await add((id) => api.addSourceFile(id, file));
      };
      ['dragover', 'dragenter'].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add('over'); }));
      ['dragleave', 'drop'].forEach((ev) => drop.addEventListener(ev, () => drop.classList.remove('over')));
      drop.addEventListener('drop', (e) => { e.preventDefault(); pick(e.dataTransfer.files[0]); });
      $('#src-file-input', r).addEventListener('change', (e) => { pick(e.target.files[0]); e.target.value = ''; });
    },
  });
  registerSourceTab({
    id: 'paste', label: '텍스트 붙여넣기',
    html: () => `<div class="field"><textarea class="textarea" id="src-paste" data-id="src-paste" rows="6" placeholder="기획 문서 본문을 붙여넣으세요 (최대 1MB)"></textarea>
      <div class="row"><span class="help" id="paste-size">0 KB / 1 MB</span><span class="spacer"></span><button class="btn-sm" data-id="src-paste-add" id="src-paste-add">소스로 추가</button></div></div>`,
    mount: (r, add) => {
      $('#src-paste', r).addEventListener('input', (e) => {
        const n = new Blob([e.target.value]).size;
        $('#paste-size', r).textContent = `${(n / 1024).toFixed(1)} KB / 1 MB`;
        $('#paste-size', r).className = 'help' + (n > 1048576 ? ' err' : '');
      });
      $('#src-paste-add', r).addEventListener('click', async () => {
        const text = $('#src-paste', r).value.trim();
        if (!text) { toast('붙여넣은 내용이 없습니다.', 'err'); return; }
        if (await add((id) => api.addSourcePaste(id, text))) $('#src-paste', r).value = '';
      });
    },
  });

  function html() {
    return `
  <section class="screen" id="screen-generate" data-screen="generate">
    <div class="wrap"><div class="gen">
      <div class="panel">
        <div class="panel-head">소스 <span class="faint" style="font-weight:400">문서 내용은 생성 시 데이터로만 쓰입니다</span></div>
        <div class="panel-body" style="display:grid;gap:12px">
          <div class="src-tabs" role="tablist">${tabs.map((t, i) => `<button class="src-tab" role="tab" data-id="src-tab-${t.id}" data-src="${t.id}" aria-selected="${i === 0}">${esc(t.label)}</button>`).join('')}</div>
          ${tabs.map((t, i) => `<div data-srcpane="${t.id}" ${i ? 'hidden' : ''}>${t.html()}</div>`).join('')}
          <div id="src-extra"></div>
          <div class="label" style="margin-top:4px">수집한 소스 <span id="src-n" class="num">0</span></div>
          <div class="srcs" id="srcs" data-id="src-list"></div>
        </div>
      </div>
      <div style="display:grid;gap:16px">
        <div class="panel"><div class="panel-head">어디에 넣을까요</div>
          <div class="panel-body" style="display:grid;gap:10px">
            <div class="field"><span class="label">시트</span><select class="select" id="gen-target-sheet" data-id="gen-target-sheet"></select></div>
            <div class="picker" data-id="gen-target-path">
              ${[['l1', '대분류'], ['l2', '중분류'], ['l3', '소분류']].map(([k, l]) => `<div class="field"><span class="label">${l}</span>
                <select class="select" id="gen-path-${k}" data-id="gen-path-${k}"></select>
                <input class="input" id="gen-new-${k}" data-id="gen-new-${k}" placeholder="새 ${l} 이름" hidden></div>`).join('')}
            </div>
            <div class="examples" data-id="gen-style-examples" id="gen-examples"></div>
          </div></div>
        <div class="panel"><div class="panel-head">작성 프로필<span class="spacer"></span><button class="btn-sm" data-id="gen-profile-edit" id="gen-profile-edit">편집</button></div>
          <div class="panel-body" style="display:grid;gap:10px">
            <select class="select" id="gen-profile" data-id="gen-profile"></select>
            <ul class="profile-rules" id="gen-rules"></ul>
            <div id="gen-profile-editor" hidden style="display:grid;gap:8px">
              <textarea class="textarea" id="gen-rules-input" data-id="gen-rules-input" rows="6" aria-label="규칙 (한 줄에 하나)"></textarea>
              <div class="row"><input class="input" id="gen-profile-name" data-id="gen-profile-name" placeholder="저장할 프로필 이름" style="max-width:220px">
                <button class="btn-sm" data-id="gen-profile-save" id="gen-profile-save">저장</button></div>
            </div>
          </div></div>
        <div class="panel"><div class="panel-body" style="display:grid;gap:12px" id="job-panel" data-id="job-panel">
          <div class="row"><button class="btn btn-primary" data-id="gen-submit" id="gen-submit" disabled>초안 생성</button><span class="help" id="gen-hint">소스를 하나 이상 추가하세요</span></div>
          <div class="job" id="job" hidden>
            <div class="row"><b id="job-title"></b><span id="job-pill"></span><span class="spacer"></span><button class="btn-sm" data-id="job-cancel" id="job-cancel">취소</button></div>
            <div class="jsteps" id="jsteps" data-id="job-progress"></div>
            <div class="help" id="job-detail"></div>
            <div id="job-fail" hidden class="warnbox err">
              <b id="job-fail-title"></b><span id="job-fail-body"></span>
              <div class="log" data-id="job-log-tail" id="job-log"></div>
              <div class="row"><button class="btn btn-primary" data-id="job-retry" id="job-retry">실패한 섹션만 다시 생성</button>
                <button class="btn btn-ghost" data-id="job-open-review-partial" id="job-open-review-partial">살린 초안 검토</button></div>
            </div>
            <div id="job-done" hidden class="row"><span class="tag ok" id="job-done-tag"></span>
              <button class="btn btn-success" data-id="job-open-review" id="job-open-review">초안 검토로 이동</button></div>
          </div>
        </div></div>
      </div>
    </div></div>
  </section>`;
  }

  // ── 소스 목록 ────────────────────────────────────────────────
  const BUNDLE_KEY = () => `tcs-bundle:${state.suite}`;

  async function ensureBundle() {
    if (bundle.bundle_id) return bundle.bundle_id;
    const { bundle_id: id } = await api.newBundle();
    bundle = { bundle_id: id, sources: [] };
    try { sessionStorage.setItem(BUNDLE_KEY(), id); } catch (e) { /* 저장 불가 환경 */ }
    return id;
  }

  // 소스 탭이 부르는 공용 추가 함수. 성공하면 true
  async function addSource(call) {
    try {
      const id = await ensureBundle();
      const { source } = await call(id);
      bundle.sources.push(source);
      renderSources();
      toast(`${esc(source.title)} 추가 · ${source.chars.toLocaleString()}자 · 섹션 ${source.sections}개`, 'ok', [], 2000);
      return true;
    } catch (err) {
      toast(`소스를 추가하지 못했습니다: ${esc(err.message)}`, 'err');
      return false;
    }
  }
  NS.generateView.addSource = addSource;

  function renderSources() {
    $('#srcs', root).innerHTML = bundle.sources.map((s) => `<div class="src-card" data-id="src-chip">
      <div class="src-ico ${s.kind}">${ICON[s.kind] || '?'}</div>
      <div style="min-width:0"><div class="src-title">${esc(s.title)}</div><div class="src-meta"><span class="src-ref">${esc(s.ref)}</span>
        <span class="tag">${s.chars.toLocaleString()}자</span>${s.pages ? `<span class="tag">${s.pages}쪽</span>` : ''}<span class="tag">섹션 ${s.sections}</span>
        ${s.truncated ? '<span class="tag warn">잘림</span>' : ''}${s.warnings.map((w) => `<span class="tag warn">${esc(w)}</span>`).join('')}</div></div>
      <button class="icon-btn" data-id="src-chip-remove" data-sid="${s.source_id}" aria-label="소스 제거">✕</button></div>`).join('')
      || '<span class="help">아직 수집한 소스가 없습니다</span>';
    $$('[data-id="src-chip-remove"]', root).forEach((b) => b.addEventListener('click', async () => {
      await api.removeSource(bundle.bundle_id, b.dataset.sid);
      bundle.sources = bundle.sources.filter((s) => s.source_id !== b.dataset.sid);
      renderSources();
    }));
    const chars = bundle.sources.reduce((n, s) => n + s.chars, 0);
    $('#src-n', root).textContent = bundle.sources.length;
    $('#gen-submit', root).disabled = !bundle.sources.length || isRunning();
    $('#gen-hint', root).textContent = bundle.sources.length
      ? `소스 ${bundle.sources.length}개 · 약 ${chars.toLocaleString()}자 · 섹션마다 수 분 걸릴 수 있습니다`
      : '소스를 하나 이상 추가하세요';
  }

  // ── 대상 가지 ────────────────────────────────────────────────
  function children(path) {
    let nodes = state.tree;
    for (const name of path) {
      const n = nodes.find((x) => x.name === name);
      nodes = n ? n.children.filter((c) => c.level !== 'feature') : [];
    }
    return nodes;
  }
  function fillSelect(id, names, cur, allowEmpty) {
    const sel = $(`#gen-path-${id}`, root) || $('#gen-target-sheet', root);
    sel.innerHTML = (allowEmpty ? '<option value="">(없음)</option>' : '')
      + names.map((n) => `<option ${n === cur ? 'selected' : ''}>${esc(n)}</option>`).join('')
      + (id !== 'sheet' ? `<option value="__new">+ 새로 만들기…</option>` : '');
  }
  function target() {
    const sheet = $('#gen-target-sheet', root).value;
    const path = ['l1', 'l2', 'l3'].map((k) => {
      const v = $(`#gen-path-${k}`, root).value;
      return v === '__new' ? $(`#gen-new-${k}`, root).value.trim() : v;
    });
    return { sheet, path };
  }
  function renderTarget(keep = target()) {
    const sheets = state.tree.map((n) => n.name);
    const sheet = sheets.includes(keep.sheet) ? keep.sheet : sheets[0];
    $('#gen-target-sheet', root).innerHTML = sheets.map((n) => `<option ${n === sheet ? 'selected' : ''}>${esc(n)}</option>`).join('');
    const path = [];
    ['l1', 'l2', 'l3'].forEach((k, i) => {
      const names = sheet ? children([sheet, ...path]).map((n) => n.name) : [];
      const cur = names.includes(keep.path[i]) ? keep.path[i] : (i === 0 ? names[0] || '' : '');
      fillSelect(k, names, cur, i > 0);
      $(`#gen-new-${k}`, root).hidden = true;
      path.push(cur);
    });
    loadExamples();
  }
  async function loadExamples() {
    const t = target();
    if (!state.suite || !t.sheet) { $('#gen-examples', root).innerHTML = ''; return; }
    const { items, total } = await api.list(state.suite, { path: [t.sheet, ...t.path.filter(Boolean)].join('/'), status: 'approved', limit: 10 });
    $('#gen-examples', root).innerHTML = `<span class="faint">같은 가지의 문체 예시 ${Math.min(total, profile().examples || 8)}건을 함께 넣습니다 (권장 5~10건)</span>`
      + (items.length ? `<span>${items.slice(0, 4).map((c) => `· ${esc(c.case_id)} ${esc(c.feature)}`).join(' ')}</span>` : '<span class="faint">이 가지에는 예시가 없습니다</span>');
  }

  // ── 작성 프로필 ──────────────────────────────────────────────
  const profile = () => profiles.find((p) => p.name === $('#gen-profile', root).value) || profiles[0] || { rules: [], examples: 8 };
  async function loadProfiles(select) {
    profiles = (await api.profiles()).profiles;
    $('#gen-profile', root).innerHTML = profiles.map((p) => `<option ${p.name === select ? 'selected' : ''}>${esc(p.name)}</option>`).join('');
    renderRules();
  }
  function renderRules() {
    const p = profile();
    $('#gen-rules', root).innerHTML = p.rules.map((r) => `<li>${esc(r)}</li>`).join('')
      + (p.banned_phrases ? `<li>금지: ${p.banned_phrases.map((b) => `"${esc(b)}"`).join(', ')}</li>` : '');
  }

  // ── 작업 ─────────────────────────────────────────────────────
  const isRunning = () => job && ['queued', 'fetching', 'drafting', 'validating'].includes(job.status);

  async function submit(extra = {}) {
    const t = target();
    if (!t.sheet || !t.path[0]) { toast('넣을 시트와 대분류를 고르세요.', 'err'); return; }
    try {
      const res = await api.startJob(state.suite, { bundle_id: bundle.bundle_id, sheet: t.sheet, path: t.path, profile: profile().name, ...extra });
      job = res.job;
      renderJob({ job, log: '', invalid: [] });
      startPolling();
    } catch (err) {
      toast(err.code === 'JOB_RUNNING' ? '이미 실행 중인 생성 작업이 있습니다. 끝난 뒤 다시 시도하세요.' : `생성을 시작하지 못했습니다: ${esc(err.message)}`, 'err');
    }
  }
  function startPolling() {
    clearInterval(poll);
    poll = setInterval(async () => {
      const body = await api.job(job.job_id);
      job = body.job;
      renderJob(body);
      if (!isRunning()) {
        clearInterval(poll);
        await NS.library.refresh();
        await NS.refreshCounts();
        if (job.status === 'done') toast(`초안 ${job.kept}건이 준비됐습니다.`, 'ok', [{ id: 'toast-open-review', label: '검토하기', fn: () => openReview() }]);
      }
    }, 1500);
  }
  function renderJob(body) {
    const j = body.job;
    $('#job', root).hidden = false;
    $('#job-title', root).textContent = `작업 ${j.job_id}`;
    const failed = ['failed', 'cancelled'].includes(j.status);
    $('#job-pill', root).innerHTML = `<span class="pill ${failed ? 'st-rejected' : j.status === 'done' ? 'st-approved' : 'st-draft'}">${esc(j.status)}</span>`;
    const at = Math.max(STEPS.findIndex(([k]) => k === j.status), 0);
    $('#jsteps', root).innerHTML = STEPS.map(([k, l], i) => {
      const cls = j.status === 'done' || i < at ? 'done' : i === at ? (failed ? 'fail' : 'run') : '';
      return `<div class="jstep ${failed && i === 2 ? 'fail' : cls}"><div class="bar"><i></i></div><span>${l}</span></div>`;
    }).join('');
    const doneSections = j.sections.filter((s) => s.status === 'done').length;
    $('#job-detail', root).textContent = j.sections.length ? `섹션 ${doneSections}/${j.sections.length} · 초안 ${j.kept}건 · 형식 오류 ${j.invalid}건 · $${j.cost_usd}` : '';
    $('#job-cancel', root).hidden = !isRunning();
    $('#gen-submit', root).disabled = isRunning() || !bundle.sources.length;
    $('#job-done', root).hidden = j.status !== 'done';
    $('#job-done-tag', root).textContent = `초안 ${j.kept}건 · 형식 오류 ${j.invalid}건`;
    $('#job-fail', root).hidden = !failed;
    if (failed) {
      const failedSections = j.sections.filter((s) => s.status === 'failed');
      $('#job-fail-title', root).textContent = j.status === 'cancelled' ? '작업을 취소했습니다' : '일부 섹션을 만들지 못했습니다';
      $('#job-fail-body', root).textContent = `${j.reason || ''} · 살린 초안 ${j.kept}건`;
      $('#job-log', root).textContent = body.log;
      $('#job-retry', root).hidden = !failedSections.length;
      $('#job-retry', root).onclick = () => submit({ only_refs: failedSections.flatMap((s) => s.refs) });
      $('#job-open-review-partial', root).hidden = !j.kept;
    }
  }
  function openReview() {
    if (job) state.reviewJob = job.job_id;
    NS.show('review');
  }

  // 커버리지 갭 등에서 대상 가지를 채워 들어올 때
  function prefill(t) {
    renderTarget({ sheet: t.sheet, path: [...t.path, '', '', ''].slice(0, 3) });
  }

  function onShow() {
    renderTarget();
    let saved = '';
    try { saved = sessionStorage.getItem(BUNDLE_KEY()) || ''; } catch (e) { saved = ''; }
    if (saved && saved !== bundle.bundle_id) {
      api.bundle(saved).then((b) => { bundle = { bundle_id: b.bundle_id, sources: b.sources }; renderSources(); }).catch(() => {});
    }
    renderSources();
  }

  function mount(r) {
    root = r;
    $$('.src-tab', root).forEach((t) => t.addEventListener('click', () => {
      $$('.src-tab', root).forEach((x) => x.setAttribute('aria-selected', x === t));
      $$('[data-srcpane]', root).forEach((p) => { p.hidden = p.dataset.srcpane !== t.dataset.src; });
    }));
    tabs.forEach((t) => t.mount($(`[data-srcpane="${t.id}"]`, root), addSource));
    $('#gen-target-sheet', root).addEventListener('change', () => renderTarget({ sheet: $('#gen-target-sheet', root).value, path: ['', '', ''] }));
    ['l1', 'l2', 'l3'].forEach((k, i) => $(`#gen-path-${k}`, root).addEventListener('change', (e) => {
      if (e.target.value === '__new') { $(`#gen-new-${k}`, root).hidden = false; $(`#gen-new-${k}`, root).focus(); return; }
      const t = target();
      renderTarget({ sheet: t.sheet, path: t.path.map((p, j) => (j <= i ? p : '')) });
    }));
    $('#gen-profile', root).addEventListener('change', () => { renderRules(); loadExamples(); });
    $('#gen-profile-edit', root).addEventListener('click', () => {
      const ed = $('#gen-profile-editor', root);
      ed.hidden = !ed.hidden;
      $('#gen-rules-input', root).value = profile().rules.join('\n');
      $('#gen-profile-name', root).value = profile().name === '기본' ? '' : profile().name;
    });
    $('#gen-profile-save', root).addEventListener('click', async () => {
      const name = $('#gen-profile-name', root).value.trim();
      const rules = $('#gen-rules-input', root).value.split('\n').map((r) => r.trim()).filter(Boolean);
      try {
        await api.saveProfile(name, { ...profile(), rules });
        await loadProfiles(name);
        $('#gen-profile-editor', root).hidden = true;
        toast(`작성 프로필 "${esc(name)}"을 저장했습니다.`, 'ok');
      } catch (err) { toast(`저장하지 못했습니다: ${esc(err.message)}`, 'err'); }
    });
    $('#gen-submit', root).addEventListener('click', () => submit());
    $('#job-cancel', root).addEventListener('click', () => api.cancelJob(job.job_id));
    ['#job-open-review', '#job-open-review-partial'].forEach((s) => $(s, root).addEventListener('click', openReview));
    loadProfiles();
  }
})(window.TCS_NS = window.TCS_NS || {});
