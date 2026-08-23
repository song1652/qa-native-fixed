// ── Pages Management View ──

async function addPage() {
  const group   = document.getElementById('pg-group').value.trim();
  const url     = document.getElementById('pg-url').value.trim();
  const notes   = document.getElementById('pg-notes').value.trim();
  const spa     = document.getElementById('pg-spa').checked;
  const project = document.getElementById('pg-project').value.trim();
  const btn     = document.getElementById('pg-add-btn');
  const status  = document.getElementById('pg-status');

  if (!group || !url) { status.textContent = '그룹명과 URL은 필수입니다'; status.className = 'pages-form-status err'; return; }

  btn.disabled = true; btn.textContent = '추가 중...';
  status.textContent = ''; status.className = 'pages-form-status';

  try {
    const res = await fetch('/api/pages/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group, url, notes, spa, project })
    });
    const data = await res.json();
    if (data.ok) {
      status.textContent = `'${group}' 추가 완료`;
      status.className = 'pages-form-status ok';
      document.getElementById('pg-group').value   = '';
      document.getElementById('pg-url').value     = '';
      document.getElementById('pg-notes').value   = '';
      document.getElementById('pg-spa').checked   = false;
      document.getElementById('pg-project').value = '';
      showToast(`${esc(group)} 페이지 추가 완료`, 'success');
      await fetchPages();
      renderPages(document.getElementById('main'));
    } else {
      status.textContent = data.error || '추가 실패';
      status.className = 'pages-form-status err';
    }
  } catch (e) {
    status.textContent = '서버 연결 오류';
    status.className = 'pages-form-status err';
  }
  btn.disabled = false; btn.textContent = '+ 추가';
}

async function deletePage(group) {
  if (!(await safeConfirm(`'${esc(group)}' 그룹을 pages.json에서 삭제하시겠습니까?<br>(testcases/${esc(group)}/ 폴더와 케이스 파일은 유지됩니다)`))) return;
  try {
    const res = await fetch('/api/pages/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group })
    });
    const data = await res.json();
    if (data.ok) {
      showToast(`${esc(group)} 삭제 완료`, 'success');
      await fetchPages();
      renderPages(document.getElementById('main'));
    } else {
      showToast(data.error || '삭제 실패', 'error');
    }
  } catch (e) {
    showToast('서버 연결 오류', 'error');
  }
}

// ── 인라인 행 수정 ──────────────────────────────────────────────

function enterEditRow(tr, grp, c) {
  tr.classList.add('editing');
  tr.innerHTML = `
    <td colspan="5">
      <div class="pages-edit-row">
        <span class="pages-group-badge pages-edit-group">${esc(grp)}</span>
        <div class="pages-edit-fields">
          <div class="pages-edit-field">
            <label class="pages-form-label">URL</label>
            <input class="pages-form-input pages-edit-url" type="url" value="${esc(c.url || '')}">
          </div>
          <div class="pages-edit-field">
            <label class="pages-form-label">프로젝트</label>
            <input class="pages-form-input pages-edit-project" type="text"
              list="pg-project-list" value="${esc(c.project || '')}">
          </div>
          <div class="pages-edit-field">
            <label class="pages-form-label">메모</label>
            <input class="pages-form-input pages-edit-notes" type="text" value="${esc(c.notes || '')}">
          </div>
          <div class="pages-edit-field pages-edit-spa-wrap">
            <label class="pages-form-label">SPA</label>
            <input type="checkbox" class="pages-edit-spa-cb"${c.spa ? ' checked' : ''}>
          </div>
        </div>
        <div class="pages-edit-actions">
          <button class="pages-save-btn">저장</button>
          <button class="pages-cancel-btn">취소</button>
        </div>
        <span class="pages-edit-err"></span>
      </div>
    </td>`;

  tr.querySelector('.pages-save-btn').addEventListener('click', () => saveEditRow(tr, grp, c));
  tr.querySelector('.pages-cancel-btn').addEventListener('click', () => {
    fetchPages().then(() => renderPages(document.getElementById('main')));
  });
}

async function saveEditRow(tr, grp, origCfg) {
  const url     = tr.querySelector('.pages-edit-url').value.trim();
  const project = tr.querySelector('.pages-edit-project').value.trim();
  const notes   = tr.querySelector('.pages-edit-notes').value.trim();
  const spa     = tr.querySelector('.pages-edit-spa-cb').checked;
  const errEl   = tr.querySelector('.pages-edit-err');

  if (!url) { errEl.textContent = 'URL은 필수입니다'; return; }
  if (project && !/^[a-zA-Z0-9_-]+$/.test(project)) {
    errEl.textContent = 'project: 영숫자·_·- 만 허용'; return;
  }
  errEl.textContent = '';

  const saveBtn = tr.querySelector('.pages-save-btn');
  saveBtn.disabled = true; saveBtn.textContent = '저장 중...';

  try {
    const res = await fetch('/api/pages/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ group: grp, url, notes, spa, project })
    });
    const data = await res.json();
    if (data.ok) {
      showToast(`${esc(grp)} 수정 완료`, 'success');
      await fetchPages();
      renderPages(document.getElementById('main'));
    } else {
      errEl.textContent = data.error || '수정 실패';
      saveBtn.disabled = false; saveBtn.textContent = '저장';
    }
  } catch (e) {
    errEl.textContent = '서버 연결 오류';
    saveBtn.disabled = false; saveBtn.textContent = '저장';
  }
}

// ── 렌더 ──────────────────────────────────────────────────────────

function renderPages(main) {
  const pages    = (pagesData && pagesData.pages)    || {};
  const groups   = (pagesData && pagesData.groups)   || [];
  const projects = (pagesData && pagesData.projects) || [];

  // groups: [{name, cases:[], count}]
  const groupMap = {};
  groups.forEach(g => { groupMap[g.name] = g; });

  // _comment 키 제외 후 엔트리 수집
  const entries = Object.entries(pages).filter(([k]) => k !== '_comment');

  // project별로 그룹핑 ('기본'은 project 필드 없거나 빈 항목)
  const projectMap = {}; // { projectName: [[grp, cfg], ...] }
  entries.forEach(([grp, cfg]) => {
    const c = (typeof cfg === 'string') ? { url: cfg } : (cfg || {});
    const proj = (c.project && c.project.trim()) || '기본';
    if (!projectMap[proj]) projectMap[proj] = [];
    projectMap[proj].push([grp, c]);
  });

  // 정렬: '기본' 마지막, 나머지 알파벳순
  const sortedProjects = Object.keys(projectMap).sort((a, b) => {
    if (a === '기본') return 1;
    if (b === '기본') return -1;
    return a.localeCompare(b);
  });

  // datalist용 기존 project 목록
  const datalistHtml = projects.map(p => `<option value="${esc(p)}">`).join('');

  // 섹션별 테이블 HTML 빌드
  let listHtml = '';
  if (!entries.length) {
    listHtml = `<div class="pages-empty">등록된 페이지가 없습니다</div>`;
  } else {
    listHtml = sortedProjects.map(proj => {
      const rows = projectMap[proj].map(([grp, c]) => {
        const tcInfo  = groupMap[grp];
        const tcCount = tcInfo ? tcInfo.count : 0;
        const tcHtml  = tcCount > 0
          ? `<span class="pages-tc-count has-cases">${tcCount}개</span>`
          : `<span class="pages-tc-count">0개</span>`;
        const spaHtml = c.spa ? `<span class="pages-spa-badge">SPA</span>` : '';
        return `<tr data-group="${esc(grp)}">
          <td><span class="pages-group-badge">${esc(grp)}</span> ${spaHtml}</td>
          <td><span class="pages-url-text">${esc(c.url || '')}</span></td>
          <td><span class="pages-notes-text">${esc(c.notes || '')}</span></td>
          <td>${tcHtml}</td>
          <td class="pages-row-actions">
            <button class="pages-edit-btn" data-group="${esc(grp)}">수정</button>
            <button class="pages-del-btn"  data-group="${esc(grp)}">삭제</button>
          </td>
        </tr>`;
      }).join('');

      const isDefault = proj === '기본';
      return `
        <div class="pages-project-section">
          <div class="pages-project-header">
            <span class="pages-project-name${isDefault ? ' default' : ''}">${esc(proj)}</span>
            <span class="pages-project-count">${projectMap[proj].length}개</span>
          </div>
          <table class="pages-table">
            <thead><tr>
              <th>그룹명</th><th>URL</th><th>메모</th><th>케이스</th><th></th>
            </tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>`;
    }).join('');
  }

  main.innerHTML = `
    <div class="pipeline-view pages-view">
      <div class="pipeline-title">페이지 URL 관리</div>

      <div class="pages-form-card">
        <div class="pages-form-title">새 페이지 등록</div>
        <div class="pages-form-grid">
          <div class="pages-form-field">
            <label class="pages-form-label">그룹명</label>
            <input id="pg-group" class="pages-form-input" type="text" placeholder="예: login" oninput="pgValidate()">
          </div>
          <div class="pages-form-field">
            <label class="pages-form-label">URL</label>
            <input id="pg-url" class="pages-form-input" type="url" placeholder="https://example.com/page" oninput="pgValidate()">
          </div>
          <div class="pages-form-field">
            <label class="pages-form-label">프로젝트 (선택)</label>
            <input id="pg-project" class="pages-form-input" type="text"
              list="pg-project-list" placeholder="예: saucedemo" oninput="pgValidate()">
            <datalist id="pg-project-list">${datalistHtml}</datalist>
            <span id="pg-project-err" class="pages-field-err" style="display:none"></span>
          </div>
          <div class="pages-form-field">
            <label class="pages-form-label">메모 (선택)</label>
            <input id="pg-notes" class="pages-form-input" type="text" placeholder="페이지 설명">
          </div>
        </div>
        <div class="pages-form-row2">
          <label class="pages-spa-label">
            <input id="pg-spa" type="checkbox"> SPA 모드 (단일 세션 순차 실행)
          </label>
          <button id="pg-add-btn" class="pages-add-btn" onclick="addPage()" disabled>+ 추가</button>
        </div>
        <div id="pg-status" class="pages-form-status"></div>
      </div>

      <div class="pages-list-title">등록된 페이지 (${entries.length}개)</div>
      ${listHtml}
    </div>`;

  // 이벤트 바인딩 (data-group 속성 사용 — XSS 방어)
  main.querySelectorAll('.pages-del-btn').forEach(btn => {
    btn.addEventListener('click', () => deletePage(btn.dataset.group));
  });
  main.querySelectorAll('.pages-edit-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const grp = btn.dataset.group;
      const raw = pages[grp];
      const c = (typeof raw === 'string') ? { url: raw } : (raw || {});
      const tr = btn.closest('tr');
      enterEditRow(tr, grp, c);
    });
  });
}

function pgValidate() {
  const group   = (document.getElementById('pg-group')   || {}).value || '';
  const url     = (document.getElementById('pg-url')     || {}).value || '';
  const project = (document.getElementById('pg-project') || {}).value || '';
  const btn     = document.getElementById('pg-add-btn');
  const pgErr   = document.getElementById('pg-project-err');

  // project 이름 실시간 검증 (영숫자·언더스코어·하이픈만 허용)
  const projectOk = !project.trim() || /^[a-zA-Z0-9_-]+$/.test(project.trim());
  if (pgErr) {
    pgErr.textContent = projectOk ? '' : '영숫자·_·- 만 사용 가능';
    pgErr.style.display = projectOk ? 'none' : 'block';
  }

  if (btn) btn.disabled = !(group.trim() && url.trim() && projectOk);
}
