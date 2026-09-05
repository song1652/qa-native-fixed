// Import Studio — 5단계 위저드
// 컴포넌트 트리: import/COMPONENT_TREE.md 참조
// 디자인 토큰: import/DESIGN_TOKENS.md 참조

const IS = (() => {
  // ─────────────────────────────────────────
  // 상태
  // ─────────────────────────────────────────
  const state = {
    step: 1,              // 현재 단계 (1~5)
    files: [],            // GET /api/import/files 결과
    selectedFile: null,   // 선택된 파일 객체 { id, name, sheets, size, modified }
    selectedSheets: [],   // 선택된 시트명 배열
    mappings: {},         // { tc_id: "A열", title: "B열", ... }
    profiles: [],         // GET /api/import/profiles 결과
    previewResult: null,  // POST /api/import/preview 결과 (모든 시트 합산)
    sessionId: null,      // 커밋 세션 ID (단일 호환)
    sessionIds: [],       // 시트별 세션 ID 배열
    commitResult: null,   // POST /api/import/commit 결과
    snapshotId: null,     // 롤백용 스냅샷 ID
    loading: false,       // 전역 로딩 상태
    error: null,          // 에러 메시지
  };

  // 단계별 유효성 검사 규칙 (COMPONENT_TREE.md 네비게이션 규칙)
  const validators = {
    1: (s) => s.selectedFile !== null && s.selectedSheets.length > 0,
    2: (s) => ['tc_id', 'title', 'steps', 'expected'].every((f) => s.mappings[f]),
    3: (s) => s.previewResult !== null,
    4: (s) => s.commitResult !== null && !s.commitResult.error,
  };

  // TC 필드 정의 (Step2 매핑)
  const TC_FIELDS = [
    { key: 'tc_id',    label: 'TC ID',      required: true },
    { key: 'title',    label: '제목',        required: true },
    { key: 'steps',    label: '테스트 단계',  required: true },
    { key: 'expected', label: '예상 결과',   required: true },
    { key: 'priority', label: '우선순위',    required: false },
    { key: 'tags',     label: '태그',        required: false },
    { key: 'group',    label: '그룹',        required: false },
  ];

  // ─────────────────────────────────────────
  // 유틸
  // ─────────────────────────────────────────
  function escHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // A열~Z열 Excel 열 이름 목록 (26개)
  function getExcelColumns() {
    const cols = [];
    for (let i = 0; i < 26; i++) {
      cols.push(String.fromCharCode(65 + i) + '열');
    }
    return cols;
  }

  function formatSize(bytes) {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function formatDate(iso) {
    if (!iso) return '';
    try {
      return new Date(iso).toLocaleDateString('ko-KR');
    } catch (_) {
      return '';
    }
  }

  // ─────────────────────────────────────────
  // API 헬퍼
  // ─────────────────────────────────────────
  async function callApi(method, path, body) {
    const res = await fetch(path, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) throw await res.json();
    return res.json();
  }

  // ─────────────────────────────────────────
  // WizardHeader — 5단계 step indicator
  // ─────────────────────────────────────────
  function renderWizardHeader() {
    const steps = [
      { n: 1, label: '파일 선택' },
      { n: 2, label: '열 매핑' },
      { n: 3, label: '미리보기' },
      { n: 4, label: '반영 확인' },
      { n: 5, label: '완료' },
    ];

    const stepsHtml = steps.map(({ n, label }) => {
      let cls = 'is-step';
      if (n < state.step) cls += ' is-step--done';
      else if (n === state.step) cls += ' is-step--active';

      const circleContent = n < state.step ? '✓' : n;

      return `<div class="${cls}">
        <div class="is-step__circle">${circleContent}</div>
        <span class="is-step__label">${escHtml(label)}</span>
      </div>`;
    }).join('');

    return `<div class="is-wizard-header">
      <div class="is-wizard-steps">${stepsHtml}</div>
    </div>`;
  }

  // ─────────────────────────────────────────
  // Step 1: 파일 선택 (FileGrid + SheetCheckboxList)
  // ─────────────────────────────────────────
  async function renderStep1() {
    // 파일 목록 지연 로드
    if (!state.files.length) {
      try {
        const data = await callApi('GET', '/api/import/files');
        const raw = data.files || [];
        // API가 파일명 문자열 배열 또는 객체 배열 둘 다 지원
        state.files = raw.map((f) =>
          typeof f === 'string'
            ? { id: f, name: f, size: null, modified: null, sheets: [] }
            : f
        );
      } catch (_err) {
        return `<div class="is-step-inner">
          <p class="is-error-msg">파일을 불러올 수 없습니다. 서버를 확인하세요.</p>
          <button class="is-btn is-btn--secondary" onclick="IS.retryInit()">↻ 다시 시도</button>
        </div>`;
      }
    }

    const sheetSection = state.selectedFile
      ? renderSheetCheckboxList(state.selectedFile.sheets || [])
      : '';

    return `<div class="is-step-inner is-fade-in">
      <h2 class="is-step-title">Excel 파일 선택</h2>
      <p class="is-step-desc">가져올 Excel 파일을 선택하고 대상 시트를 지정하세요.</p>
      ${renderFileGrid(state.files)}
      ${sheetSection}
    </div>`;
  }

  function renderFileGrid(files) {
    if (!files.length) {
      return `<p class="is-empty-text">import/ 폴더에 .xlsx 파일이 없습니다.</p>`;
    }
    const cards = files.map(renderFileCard).join('');
    return `<div class="is-file-grid">${cards}</div>`;
  }

  function renderFileCard(file) {
    const isSelected = state.selectedFile && state.selectedFile.id === file.id;
    const cls = `is-file-card${isSelected ? ' is-file-card--selected' : ''}`;

    const sizeStr = formatSize(file.size);
    const dateStr = formatDate(file.modified);
    const meta = [sizeStr, dateStr].filter(Boolean).join(' · ');
    const sheetCount = Array.isArray(file.sheets) ? file.sheets.length : 0;

    return `<div class="${cls}" data-file-id="${escHtml(file.id)}" onclick="IS.selectFile(this.dataset.fileId)" role="button" tabindex="0"
              onkeydown="if(event.key==='Enter'||event.key===' ')IS.selectFile(this.dataset.fileId)">
      <div class="is-file-card__name" title="${escHtml(file.name)}">
        <span class="is-file-icon">📄</span> ${escHtml(file.name)}
      </div>
      ${meta ? `<div class="is-file-card__meta">${escHtml(meta)}</div>` : ''}
      ${sheetCount ? `<div class="is-file-card__meta">${sheetCount}개 시트</div>` : ''}
    </div>`;
  }

  function renderSheetCheckboxList(sheets) {
    const selectedCount = state.selectedSheets.length;

    if (!sheets.length) {
      return `<div class="is-sheet-section">
        <h3 class="is-sheet-title">시트 선택</h3>
        <p class="is-empty-text">시트 정보가 없습니다. 기본 시트(Sheet1)를 사용합니다.</p>
      </div>`;
    }

    const items = sheets.map((sheet) => {
      const checked = state.selectedSheets.includes(sheet);
      return `<label class="is-sheet-item" data-sheet="${escHtml(sheet)}">
        <input type="checkbox" ${checked ? 'checked' : ''}
               onchange="IS.toggleSheet(this.closest('.is-sheet-item').dataset.sheet)" />
        <span class="is-sheet-name">${escHtml(sheet)}</span>
      </label>`;
    }).join('');

    return `<div class="is-sheet-section is-fade-in">
      <h3 class="is-sheet-title">
        시트 선택
        <span class="is-count-badge">${selectedCount}개 선택됨</span>
      </h3>
      <div class="is-sheet-list">${items}</div>
    </div>`;
  }

  // ─────────────────────────────────────────
  // Step 2: 열 매핑 (3패널 MappingPanel)
  // ─────────────────────────────────────────
  function renderStep2() {
    const excelColumns = getExcelColumns();

    const leftPanel = `<div class="is-mapping-panel">
      <div class="is-mapping-panel-hd">Excel 열</div>
      <div class="is-mapping-panel-body">
        ${excelColumns.map((col) => {
          const isConnected = Object.values(state.mappings).includes(col);
          return `<div class="is-mapping-item${isConnected ? ' is-mapping-item--connected' : ''}">${escHtml(col)}</div>`;
        }).join('')}
      </div>
    </div>`;

    const centerPanel = `<div class="is-mapping-arrows">
      ${TC_FIELDS.map(() => '<span class="is-arrow-icon">→</span>').join('')}
    </div>`;

    const rightPanel = `<div class="is-mapping-panel">
      <div class="is-mapping-panel-hd">TC 필드</div>
      <div class="is-mapping-panel-body">
        ${TC_FIELDS.map(({ key, label, required }) => {
          const val = state.mappings[key] || '';
          const opts = ['', ...excelColumns].map((col) =>
            `<option value="${escHtml(col)}" ${col === val ? 'selected' : ''}>${col ? escHtml(col) : '— 선택 안 함 —'}</option>`
          ).join('');
          return `<div class="is-mapping-item${val ? ' is-mapping-item--connected' : ''}">
            <label class="is-field-label">
              ${escHtml(label)}${required ? '<span class="is-required" aria-label="필수"> *</span>' : ''}
            </label>
            <select class="is-select" data-field="${escHtml(key)}" onchange="IS.setMapping(this.dataset.field, this.value)">
              ${opts}
            </select>
          </div>`;
        }).join('')}
      </div>
    </div>`;

    return `<div class="is-step-inner is-fade-in">
      <h2 class="is-step-title">열 매핑</h2>
      <p class="is-step-desc">Excel 열과 TC 필드를 연결하세요. <span class="is-required">*</span> 는 필수 항목입니다.</p>
      ${renderProfileToolbar()}
      <div class="is-mapping-editor">
        ${leftPanel}
        ${centerPanel}
        ${rightPanel}
      </div>
    </div>`;
  }

  function renderProfileToolbar() {
    const profileOpts = state.profiles.length
      ? state.profiles.map((p) =>
          `<option value="${escHtml(p.id)}">${escHtml(p.name)}</option>`
        ).join('')
      : '';

    const profileListItems = state.profiles.map((p) => {
      return `<div class="is-profile-item" data-profile-id="${escHtml(p.id)}">
        <span class="is-profile-item__name">${escHtml(p.name)}</span>
        <button class="is-profile-delete-btn"
                onclick="IS.deleteProfile(this.closest('.is-profile-item').dataset.profileId)"
                title="프로필 삭제"
                aria-label="${escHtml(p.name)} 삭제">🗑️</button>
      </div>`;
    }).join('');

    return `<div class="is-profile-toolbar-wrap">
      <div class="is-profile-toolbar">
        ${state.profiles.length ? `
          <select class="is-select is-select--sm" id="is-profile-select">
            <option value="">프로필 선택...</option>
            ${profileOpts}
          </select>
          <button class="is-btn is-btn--secondary" onclick="IS.loadProfile()">불러오기</button>
        ` : ''}
        <button class="is-btn is-btn--secondary" onclick="IS.saveProfile()">💾 프로필 저장</button>
      </div>
      ${profileListItems ? `<div class="is-profile-list">${profileListItems}</div>` : ''}
    </div>`;
  }

  // ─────────────────────────────────────────
  // Step 3: 미리보기
  // ─────────────────────────────────────────
  function renderStep3() {
    if (state.loading) {
      return `<div class="is-step-inner is-step-loading">
        <div class="is-spinner"></div>
        <p class="is-loading-text">미리보기 생성 중...</p>
      </div>`;
    }

    if (!state.previewResult) {
      return `<div class="is-step-inner">
        <p class="is-error-msg">미리보기 생성에 실패했습니다.</p>
        <button class="is-btn is-btn--secondary" onclick="IS.prev()">← 이전 단계로</button>
      </div>`;
    }

    const { summary = {}, rows = [] } = state.previewResult;

    return `<div class="is-step-inner is-fade-in">
      <h2 class="is-step-title">가져오기 미리보기</h2>
      ${renderSummaryCards(summary)}
      <div class="is-preview-actions">
        <button class="is-btn is-btn--secondary" onclick="IS.downloadCsv()">⬇ CSV 내보내기</button>
      </div>
      <div class="is-preview-table-wrap">
        ${renderPreviewTable(rows)}
      </div>
    </div>`;
  }

  function renderSummaryCards(summary) {
    const cards = [
      { key: 'added',    label: '추가',    status: 'added' },
      { key: 'updated',  label: '업데이트', status: 'updated' },
      { key: 'conflict', label: '충돌',    status: 'conflict' },
      { key: 'error',    label: '오류',    status: 'error' },
    ];

    return `<div class="is-summary-cards">
      ${cards.map(({ key, label, status }) => `
        <div class="is-summary-card" data-status="${status}">
          <div class="is-summary-card__count">${summary[key] ?? 0}</div>
          <div class="is-summary-card__label">${label}</div>
        </div>
      `).join('')}
    </div>`;
  }

  function renderPreviewTable(rows) {
    if (!rows.length) {
      return `<p class="is-empty-text">미리보기 데이터가 없습니다.</p>`;
    }

    const STATUS_LABEL = {
      added: '추가', updated: '업데이트', conflict: '충돌', error: '오류', same: '동일',
    };

    const tbody = rows.map((row) => `
      <tr data-status="${escHtml(row.status)}">
        <td>${escHtml(String(row.row ?? ''))}</td>
        <td>${escHtml(row.tc_id ?? '')}</td>
        <td>${escHtml(row.title ?? '')}</td>
        <td>${escHtml(row.group ?? '')}</td>
        <td>
          <span class="is-badge is-badge--${escHtml(row.status)}">
            ${STATUS_LABEL[row.status] ?? escHtml(row.status)}
          </span>
        </td>
        <td>${escHtml(row.reason ?? '')}</td>
      </tr>
    `).join('');

    return `<table class="is-preview-table">
      <thead>
        <tr>
          <th>행</th><th>TC ID</th><th>제목</th><th>그룹</th><th>상태</th><th>사유</th>
        </tr>
      </thead>
      <tbody>${tbody}</tbody>
    </table>`;
  }

  // ─────────────────────────────────────────
  // Step 4: 반영 확인
  // ─────────────────────────────────────────
  function renderStep4() {
    const summary = state.previewResult?.summary ?? {};
    const added   = summary.added   ?? 0;
    const updated = summary.updated ?? 0;
    const skipped = (summary.same ?? 0) + (summary.conflict ?? 0);

    return `<div class="is-step-inner is-fade-in">
      <h2 class="is-step-title">파일에 반영하기</h2>
      <div class="is-commit-summary">
        <p class="is-commit-intro">다음 내용을 <code>testcases/</code> 폴더에 적용합니다:</p>
        <ul class="is-commit-list">
          <li>신규 TC: <strong class="is-count-added">${added}건</strong></li>
          <li>업데이트 TC: <strong class="is-count-updated">${updated}건</strong></li>
          ${skipped ? `<li>스킵 (동일/충돌): ${skipped}건</li>` : ''}
        </ul>
      </div>
      <div class="is-commit-actions">
        <button class="is-btn is-btn--primary" onclick="IS.commit()"
                ${state.loading ? 'disabled aria-disabled="true"' : ''}>
          ${state.loading
            ? '<span class="is-spinner is-spinner--sm"></span> 처리 중...'
            : '✅ 파일에 적용'}
        </button>
      </div>
      ${state.error ? `<p class="is-error-msg">${escHtml(state.error)}</p>` : ''}
    </div>`;
  }

  // ─────────────────────────────────────────
  // Step 5: 완료
  // ─────────────────────────────────────────
  function renderStep5() {
    const cr = state.commitResult ?? {};

    return `<div class="is-step-inner is-step-done is-fade-in">
      <div class="is-done-icon" aria-hidden="true">🎉</div>
      <h2 class="is-step-title">가져오기 완료!</h2>
      <div class="is-result-summary">
        <p>커밋: <strong>${cr.committed ?? 0}건</strong>
           &nbsp;·&nbsp;
           스킵: <strong>${cr.skipped ?? 0}건</strong>
        </p>
      </div>
      <div class="is-done-actions">
        ${state.snapshotId
          ? `<button class="is-btn is-btn--secondary" onclick="IS.rollback()">↩ 롤백</button>`
          : ''}
        <button class="is-btn is-btn--primary" onclick="IS.viewTc()">📂 테스트케이스 보기</button>
      </div>
    </div>`;
  }

  // ─────────────────────────────────────────
  // 이벤트 핸들러 (전역 IS.xxx() 노출)
  // ─────────────────────────────────────────

  /** 파일 선택 — targeted DOM update (카드 선택 표시 + 시트 섹션만 교체) */
  function selectFile(fileId) {
    const file = state.files.find((f) => f.id === fileId);
    if (!file) return;
    state.selectedFile = file;
    state.selectedSheets = [];
    if (!Array.isArray(file.sheets) || !file.sheets.length) {
      file.sheets = ['Sheet1'];
    }
    // 파일 카드 선택 클래스만 토글
    document.querySelectorAll('.is-file-card').forEach((card) => {
      card.classList.toggle('is-file-card--selected', card.dataset.fileId === fileId);
    });
    // 시트 섹션만 교체 (전체 재렌더 없음)
    const newSheetHtml = renderSheetCheckboxList(file.sheets);
    const existing = document.querySelector('.is-sheet-section');
    if (existing) {
      existing.outerHTML = newSheetHtml;
    } else {
      const grid = document.querySelector('.is-file-grid');
      if (grid) grid.insertAdjacentHTML('afterend', newSheetHtml);
    }
    _updateNavButtons();
  }

  /** 시트 체크박스 토글 — targeted DOM update (깜빡임 없음) */
  function toggleSheet(sheetName) {
    const idx = state.selectedSheets.indexOf(sheetName);
    if (idx >= 0) {
      state.selectedSheets.splice(idx, 1);
    } else {
      state.selectedSheets.push(sheetName);
    }
    // 체크박스 상태만 갱신 (전체 재렌더 없음)
    document.querySelectorAll('.is-sheet-item').forEach((label) => {
      const input = label.querySelector('input[type=checkbox]');
      if (input) input.checked = state.selectedSheets.includes(label.dataset.sheet);
    });
    const badge = document.querySelector('.is-count-badge');
    if (badge) badge.textContent = `${state.selectedSheets.length}개 선택됨`;
    _updateNavButtons();
  }

  /** 열 매핑 변경 — targeted DOM update */
  function setMapping(field, col) {
    if (col) {
      state.mappings[field] = col;
    } else {
      delete state.mappings[field];
    }
    // 해당 매핑 아이템 connected 클래스만 토글
    const sel = document.querySelector(`select[data-field="${field}"]`);
    if (sel) {
      const item = sel.closest('.is-mapping-item');
      if (item) item.classList.toggle('is-mapping-item--connected', !!col);
    }
    _updateNavButtons();
  }

  /** 프로필 저장 */
  async function saveProfile() {
    const name = prompt('프로필 이름을 입력하세요:');
    if (!name || !name.trim()) return;
    try {
      await callApi('POST', '/api/import/profiles', { name: name.trim(), mappings: state.mappings });
      const data = await callApi('GET', '/api/import/profiles');
      state.profiles = data.profiles || [];
      render();
    } catch (err) {
      alert(`저장 실패: ${err.error || String(err)}`);
    }
  }

  /** 프로필 삭제 */
  async function deleteProfile(profileId) {
    const profile = state.profiles.find((p) => p.id === profileId);
    const name = profile ? profile.name : profileId;
    if (!confirm(`"${name}" 프로필을 삭제하시겠습니까?`)) return;
    try {
      await callApi('POST', '/api/import/profiles/delete', { id: profileId });
      const data = await callApi('GET', '/api/import/profiles');
      state.profiles = data.profiles || [];
      render();
    } catch (err) {
      alert(`삭제 실패: ${err.error || String(err)}`);
    }
  }

  /** 프로필 불러오기 */
  function loadProfile() {
    const sel = document.getElementById('is-profile-select');
    if (!sel) return;
    const profileId = sel.value;
    if (!profileId) return;
    const profile = state.profiles.find((p) => p.id === profileId);
    if (profile) {
      state.mappings = { ...profile.mappings };
      render();
    }
  }

  /** 초기화 재시도 */
  async function retryInit() {
    state.files = [];
    state.error = null;
    await render();
  }

  /** CSV 다운로드 */
  function downloadCsv() {
    if (!state.sessionId) return;
    window.location.href = `/api/import/preview/csv?session_id=${encodeURIComponent(state.sessionId)}`;
  }

  /** 커밋 실행 — 선택된 모든 시트(세션)를 순차 커밋 후 결과 합산 */
  async function commit() {
    if (state.loading) return;
    state.loading = true;
    state.error = null;
    await render();
    try {
      const ids = state.sessionIds.length > 0
        ? state.sessionIds
        : (state.sessionId ? [state.sessionId] : []);
      let totalCommitted = 0, totalSkipped = 0, lastSnap = null;
      for (const sid of ids) {
        const result = await callApi('POST', '/api/import/commit', { session_id: sid });
        totalCommitted += result.committed ?? 0;
        totalSkipped   += result.skipped   ?? 0;
        if (result.snapshot_id) lastSnap = result.snapshot_id;
      }
      state.commitResult = { committed: totalCommitted, skipped: totalSkipped, snapshot_id: lastSnap };
      state.snapshotId = lastSnap;
      state.loading = false;
      goTo(5);
      _playConfetti();
    } catch (err) {
      state.error = '커밋에 실패했습니다. 다시 시도하세요.';
      state.loading = false;
      await render();
    }
  }

  /** 롤백 실행 */
  async function rollback() {
    if (!state.snapshotId) return;
    if (!confirm('롤백하면 방금 반영한 변경이 취소됩니다. 계속하시겠습니까?')) return;
    try {
      await callApi('POST', '/api/import/rollback', { snapshot_id: state.snapshotId });
      // 상태 초기화 후 Step1으로
      state.commitResult = null;
      state.previewResult = null;
      state.sessionId = null;
      state.sessionIds = [];
      state.snapshotId = null;
      goTo(1);
    } catch (err) {
      alert(`롤백 실패: ${err.error || String(err)}`);
    }
  }

  /** testcases 페이지 이동 */
  function viewTc() {
    window.location.hash = '#/testcases';
  }

  // ─────────────────────────────────────────
  // 위저드 네비게이션
  // ─────────────────────────────────────────
  function canNext() {
    const validator = validators[state.step];
    return validator ? validator(state) : state.step < 5;
  }

  function goTo(step) {
    state.error = null;
    state.step = step;
    render();
  }

  async function next() {
    if (!canNext()) return;
    // Step2 → Step3: 미리보기 API 호출
    if (state.step === 2) {
      await _loadPreview();
      if (!state.previewResult) return; // 실패 시 이동 안 함
    }
    goTo(state.step + 1);
  }

  function prev() {
    if (state.step > 1) {
      state.error = null;
      goTo(state.step - 1);
    }
  }

  // ─────────────────────────────────────────
  // 내부 헬퍼
  // ─────────────────────────────────────────

  /** 미리보기 API 호출 — 선택된 모든 시트 순회 후 결과 합산 */
  async function _loadPreview() {
    state.loading = true;
    state.previewResult = null;
    state.error = null;
    state.sessionIds = [];
    state.sessionId = null;
    await render();
    try {
      const totalSummary = { added: 0, updated: 0, conflict: 0, error: 0, same: 0 };
      let allRows = [];
      for (const sheetName of state.selectedSheets) {
        const result = await callApi('POST', '/api/import/preview', {
          file_id: state.selectedFile.id,
          sheet_name: sheetName,
          mappings: state.mappings,
        });
        state.sessionIds.push(result.session_id);
        for (const key of Object.keys(totalSummary)) {
          totalSummary[key] = (totalSummary[key] || 0) + (result.summary?.[key] || 0);
        }
        allRows = allRows.concat((result.rows || []).map((r) => ({ ...r, _sheet: sheetName })));
      }
      state.previewResult = { summary: totalSummary, rows: allRows };
      state.sessionId = state.sessionIds[0] ?? null;
    } catch (err) {
      state.error = '미리보기 생성에 실패했습니다.';
    } finally {
      state.loading = false;
    }
  }

  /** 다음 버튼 활성/비활성 갱신 (DOM 직접 조작, 전체 재렌더 방지) */
  function _updateNavButtons() {
    const nextBtn = document.querySelector('.is-nav-next');
    if (!nextBtn) return;
    if (canNext()) {
      nextBtn.removeAttribute('disabled');
      nextBtn.removeAttribute('aria-disabled');
    } else {
      nextBtn.setAttribute('disabled', '');
      nextBtn.setAttribute('aria-disabled', 'true');
    }
  }

  /** 시트 체크박스 섹션만 부분 갱신 */
  function _refreshSheetSection() {
    const section = document.querySelector('.is-sheet-section');
    if (!section || !state.selectedFile) return;
    section.outerHTML = renderSheetCheckboxList(state.selectedFile.sheets || []);
    _updateNavButtons();
  }

  /** 컨페티 완료 애니메이션 */
  function _playConfetti() {
    const colors = ['#8B5CF6', '#22C55E', '#3B82F6', '#F59E0B', '#EF4444', '#EC4899'];
    for (let i = 0; i < 60; i++) {
      const el = document.createElement('div');
      el.className = 'is-confetti-piece';
      const size = 6 + Math.random() * 6;
      el.style.cssText = [
        `left: ${Math.random() * 100}vw`,
        `top: -12px`,
        `width: ${size}px`,
        `height: ${size}px`,
        `background: ${colors[Math.floor(Math.random() * colors.length)]}`,
        `border-radius: ${Math.random() > 0.5 ? '50%' : '2px'}`,
        `animation-delay: ${(Math.random() * 600).toFixed(0)}ms`,
        `animation-duration: ${(1200 + Math.random() * 800).toFixed(0)}ms`,
      ].join(';');
      document.body.appendChild(el);
      setTimeout(() => el.remove(), 2500);
    }
  }

  // ─────────────────────────────────────────
  // 메인 렌더 (async — Step1이 async fetch 포함)
  // ─────────────────────────────────────────
  // RAF 디바운스: 연속 render() 호출을 1프레임으로 합침
  let _renderRaf = null;
  async function render() {
    if (_renderRaf) return; // 이미 예약됨 → 스킵
    _renderRaf = requestAnimationFrame(async () => {
      _renderRaf = null;
      await _doRender();
    });
  }

  async function _doRender() {
    const container = document.getElementById('import-studio-root');
    if (!container) return;

    // Step 콘텐츠 생성 (Step1만 async)
    let stepHtml = '';
    switch (state.step) {
      case 1: stepHtml = await renderStep1(); break;
      case 2: stepHtml = renderStep2();       break;
      case 3: stepHtml = renderStep3();       break;
      case 4: stepHtml = renderStep4();       break;
      case 5: stepHtml = renderStep5();       break;
      default: stepHtml = '';
    }

    // 이전/다음 네비게이션 버튼
    const prevBtn = state.step > 1
      ? `<button class="is-btn is-btn--secondary is-nav-prev" onclick="IS.prev()">← 이전</button>`
      : `<span></span>`;

    const isLast = state.step === 5;
    const nextDisabled = !canNext() || state.loading;
    const nextLabel = isLast ? '' : (state.step === 4 ? '' : '다음 →');
    const nextBtn = !isLast
      ? `<button class="is-btn is-btn--primary is-nav-next"
             onclick="IS.next()"
             ${nextDisabled ? 'disabled aria-disabled="true"' : ''}>
           ${nextLabel || '다음 →'}
         </button>`
      : '';

    // 에러 배너
    const errorBanner = state.error
      ? `<div class="is-error-banner" role="alert">${escHtml(state.error)}</div>`
      : '';

    container.innerHTML = `<div class="import-studio">
      ${renderWizardHeader()}
      ${errorBanner}
      <div class="is-step-content">
        ${stepHtml}
      </div>
      <div class="is-wizard-nav">
        ${prevBtn}
        ${nextBtn}
      </div>
    </div>`;
  }

  // ─────────────────────────────────────────
  // 초기화
  // ─────────────────────────────────────────
  async function init(containerId) {
    const el = typeof containerId === 'string'
      ? (document.getElementById(containerId.replace(/^#/, '')) ||
         document.querySelector(containerId))
      : containerId;

    if (!el) {
      console.warn('[ImportStudio] container not found:', containerId);
      return;
    }

    el.id = 'import-studio-root';

    // 매핑 프로필 사전 로드 (실패해도 무시)
    try {
      const data = await callApi('GET', '/api/import/profiles');
      state.profiles = data.profiles || [];
    } catch (_) {
      state.profiles = [];
    }

    await render();
  }

  // ─────────────────────────────────────────
  // Public API — onclick="IS.xxx()" 전역 접근용
  // ─────────────────────────────────────────
  return {
    init,
    // 네비게이션
    next,
    prev,
    goTo,
    // Step1
    selectFile,
    toggleSheet,
    retryInit,
    // Step2
    setMapping,
    saveProfile,
    loadProfile,
    deleteProfile,
    // Step3
    downloadCsv,
    // Step4
    commit,
    // Step5
    rollback,
    viewTc,
  };
})();

export default IS;
