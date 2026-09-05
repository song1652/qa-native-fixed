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
    selectedSources: [],  // [{ fileId, sheets: [] }] — 한 번의 run으로 묶을 원본
    mappings: {},         // 모든 원본에 적용되는 공통 매핑
    sourceMappings: {},   // { "fileId::sheet": { tc_id: "A열" } } 예외 매핑
    activeMappingSource: '',
    profiles: [],         // GET /api/import/profiles 결과
    previewResult: null,  // POST /api/import/preview 결과 (모든 시트 합산)
    runId: null,          // preview/commit/result/rollback을 잇는 단일 작업 ID
    idempotencyKey: null, // 같은 run의 중복 커밋을 안전하게 재조정하기 위한 키
    commitResult: null,   // POST /api/import/commit 결과
    rollbackResult: null, // 롤백 후에도 완료 화면에서 최종 상태를 보존
    decisions: {},        // { rowKey: 'exclude' } — 충돌 행은 명시적 결정 필수
    modal: null,          // 앱 내부 입력/확인 대화상자
    loading: false,       // 전역 로딩 상태
    error: null,          // 에러 메시지
    policy: 'skip-conflict', // Step4 정책 선택
    activeFilter: 'all',     // Step3 필터
  };

  // 단계별 유효성 검사 규칙
  // Step3: 충돌 미처리도 통과 — 충돌은 Step4 정책(skip-conflict/overwrite)으로 일괄 처리
  const validators = {
    1: (s) => s.selectedSources.length > 0 && s.selectedSources.every((source) => source.sheets.length > 0),
    2: (s) => ['tc_id', 'title', 'precondition', 'steps', 'expected'].every((f) => s.mappings[f]),
    3: (s) => s.previewResult !== null,
    4: (s) => s.commitResult !== null && s.commitResult.status === 'committed',
  };

  // TC 필드 정의 (Step2 매핑)
  const TC_FIELDS = [
    { key: 'tc_id',         label: 'TC ID',      required: true },
    { key: 'title',         label: '제목',        required: true },
    { key: 'precondition',  label: '사전 조건',   required: true },
    { key: 'steps',         label: '테스트 단계', required: true },
    { key: 'expected',      label: '예상 결과',   required: true },
    { key: 'priority',      label: '우선순위',    required: false },
    { key: 'tags',          label: '태그',        required: false },
    { key: 'group',         label: '그룹',        required: false },
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

  function errorMessage(err, fallback) {
    return err?.error || err?.message || fallback;
  }

  function rowKey(row) {
    return [
      row.source_file_id || row.file_id || row.file_name || row.source_file || '',
      row.sheet_name || row.source_sheet || '',
      row.source_row ?? row.row ?? '',
      row.tc_id || '',
    ].join('::');
  }

  function unresolvedConflictCount(s = state) {
    const rows = s.previewResult?.rows || [];
    return rows.filter((row) => row.status === 'conflict' && s.decisions[rowKey(row)] !== 'exclude').length;
  }

  function makeIdempotencyKey(runId) {
    if (window.crypto?.randomUUID) return `${runId}:${window.crypto.randomUUID()}`;
    return `${runId}:${Date.now()}:${Math.random().toString(16).slice(2)}`;
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
    let data;
    try {
      data = await res.json();
    } catch (_) {
      data = { error: `서버가 올바른 JSON을 반환하지 않았습니다. (HTTP ${res.status})` };
    }
    if (!res.ok || data?.ok === false) throw data;
    return data;
  }

  // ─────────────────────────────────────────
  // WizardHeader — 5단계 step indicator
  // ─────────────────────────────────────────
  function renderWizardHeader() {
    const steps = [
      { n: 1, label: '파일 선택' },
      { n: 2, label: '열 매핑' },
      { n: 3, label: '미리보기' },
      { n: 4, label: '안전한 반영' },
      { n: 5, label: '완료' },
    ];

    const parts = [];
    steps.forEach(({ n, label }, i) => {
      const done   = n < state.step;
      const active = n === state.step;
      const circleCls = `step-circle${done ? ' done' : active ? ' active' : ''}`;
      const labelCls  = `step-label${active ? ' active' : ''}`;
      parts.push(`<div class="step-item">
        <div class="${circleCls}">${done ? '✓' : n}</div>
        <div class="${labelCls}">${escHtml(label)}</div>
      </div>`);
      if (i < steps.length - 1) {
        parts.push(`<div class="step-line${done ? ' done' : ''}"></div>`);
      }
    });

    return parts.join('');
  }

  // ─────────────────────────────────────────
  // Step 1: 파일 선택
  // ─────────────────────────────────────────
  const SAFE_NOTE_HTML = `<div class="safe-note">
    <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor" style="color:var(--accent);opacity:.7">
      <path fill-rule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
    </svg>
    원본 파일은 변경되지 않습니다
  </div>`;

  async function renderStep1() {
    if (!state.files.length) {
      try {
        const data = await callApi('GET', '/api/import/files');
        const raw = data.files || [];
        state.files = raw.map((f) =>
          typeof f === 'string'
            ? { id: f, name: f, size: null, modified: null, sheets: [] }
            : f
        );
      } catch (_err) {
        const canGo = validators[1](state);
        return `<div class="content">
          <p style="color:var(--error);margin-bottom:12px">파일을 불러올 수 없습니다. 서버를 확인하세요.</p>
          <button class="btn btn-ghost" onclick="IS.retryInit()">↻ 다시 시도</button>
        </div>
        <div class="bottom-bar">
          ${SAFE_NOTE_HTML}
          <div class="spacer"></div>
          <button class="btn btn-primary" disabled>다음: 열 매핑 →</button>
        </div>`;
      }
    }

    const canGo = validators[1](state);
    const selCount = state.selectedSources.filter((s) => s.sheets.length > 0).length;

    return `<div class="content">
      <p style="font-size:13px;color:var(--text2);margin-bottom:16px">import/ 폴더의 Excel 파일을 선택하고, 가져올 시트와 대상 그룹을 지정하세요.</p>
      ${renderFileGrid(state.files)}
    </div>
    <div class="bottom-bar">
      ${SAFE_NOTE_HTML}
      <div class="spacer"></div>
      <span style="font-size:12px;color:var(--text3);margin-right:4px">${selCount}개 파일 선택됨</span>
      <button class="btn btn-primary" data-testid="next-button" onclick="IS.next()" ${canGo ? '' : 'disabled'}>다음: 열 매핑 →</button>
    </div>`;
  }

  function renderFileGrid(files) {
    if (!files.length) {
      return `<p style="color:var(--text3);font-size:12px">import/ 폴더에 .xlsx 파일이 없습니다.</p>`;
    }
    const cards = files.map(renderFileCard).join('');
    return `<div class="file-grid">${cards}</div>`;
  }

  function renderFileCard(file) {
    const unavailableReason = file.error || (!Array.isArray(file.sheets) || !file.sheets.length
      ? '가져올 수 있는 시트가 없습니다.'
      : '');
    const unavailable = Boolean(unavailableReason);
    const isSelected = state.selectedSources.some((source) => source.fileId === file.id);
    const source = state.selectedSources.find((s) => s.fileId === file.id);
    const cls = `file-card${isSelected ? ' selected' : ''}${unavailable ? ' unavailable' : ''}`;

    const sizeStr = formatSize(file.size);
    const dateStr = formatDate(file.modified);
    const sheetCount = Array.isArray(file.sheets) ? file.sheets.length : 0;
    const metaParts = [sizeStr, dateStr, sheetCount ? `${sheetCount}개 시트` : ''].filter(Boolean);
    const meta = metaParts.join(' · ');

    const sheetsHtml = isSelected && source && Array.isArray(file.sheets) && file.sheets.length
      ? `<div class="file-sheets" onclick="event.stopPropagation()">
          ${file.sheets.map((sheet) => {
            const checked = source.sheets.includes(sheet);
            const rowCount = (typeof sheet === 'object' ? sheet.rows : null)
              || (file.sheet_rows && file.sheet_rows[typeof sheet === 'object' ? sheet.name : sheet])
              || '';
            const sheetName = typeof sheet === 'object' ? sheet.name : sheet;
            return `<div class="sheet-row" onclick="event.stopPropagation()">
              <input type="checkbox" data-testid="sheet-checkbox" ${checked ? 'checked' : ''}
                     data-file-id="${escHtml(file.id)}" data-sheet="${escHtml(sheetName)}"
                     onclick="event.stopPropagation()"
                     onchange="IS.toggleSheet(this.dataset.fileId, this.dataset.sheet)" />
              <span class="sheet-name">${escHtml(sheetName)}</span>
              ${rowCount ? `<span class="sheet-rows">${rowCount}행</span>` : ''}
            </div>`;
          }).join('')}
        </div>`
      : '';

    const clickAttrs = unavailable
      ? 'aria-disabled="true" tabindex="-1"'
      : `onclick="IS.selectFile(this.dataset.fileId)" role="checkbox" aria-checked="${isSelected}" tabindex="0"
         onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();IS.selectFile(this.dataset.fileId)}"`;

    return `<div class="${cls}" data-testid="file-card" data-file-id="${escHtml(file.id)}" ${clickAttrs}>
      <div class="file-card-head">
        <div class="excel-icon">X</div>
        <div style="flex:1;min-width:0">
          <div class="file-name" title="${escHtml(file.name)}">${escHtml(file.name)}</div>
          ${meta ? `<div class="file-meta">${escHtml(meta)}</div>` : ''}
        </div>
        <div class="file-check">${isSelected ? '✓' : ''}</div>
      </div>
      ${unavailable ? `<div style="color:var(--error);font-size:11px;margin-top:8px" data-testid="file-unavailable-message">사용 불가: ${escHtml(unavailableReason)}</div>` : ''}
      ${sheetsHtml}
    </div>`;
  }

  // renderSheetCheckboxList은 Step1에서 파일카드 내부로 통합됨 — 하위 호환 유지
  function renderSheetCheckboxList(file, source) {
    return '';
  }

  // ─────────────────────────────────────────
  // Step 2: 열 매핑 (3열 레이아웃)
  // ─────────────────────────────────────────
  function renderStep2() {
    const excelColumns = getExcelColumns();
    const sources = getSelectedSheetSources();
    const canGo = validators[2](state);

    // 왼쪽 패널: 선택한 파일 목록
    const leftPanel = `<div class="panel">
      <div class="panel-header">
        <div class="panel-title">선택한 파일</div>
        <div class="panel-badge">${state.selectedSources.length}</div>
      </div>
      <div class="panel-body">
        ${state.selectedSources.map((source) => {
          const file = state.files.find((f) => f.id === source.fileId);
          const name = file ? file.name : source.fileId;
          const sheetNames = source.sheets.join(', ');
          return `<div class="mini-file">
            <div class="mini-excel">X</div>
            <div class="mini-name" title="${escHtml(name)}">${escHtml(name)}</div>
            <span class="mini-ok">✓</span>
          </div>
          ${sheetNames ? `<div class="mini-meta">${escHtml(sheetNames)}</div>` : ''}`;
        }).join('')}
      </div>
    </div>`;

    // 가운데 패널: 프로필 바 + 매핑 행
    const mapRows = TC_FIELDS.map(({ key, label, required }) => {
      const val = state.mappings[key] || '';
      const opts = ['', ...excelColumns].map((col) =>
        `<option value="${escHtml(col)}" ${col === val ? 'selected' : ''}>${col ? escHtml(col) : '— 선택 안 함 —'}</option>`
      ).join('');
      return `<div class="map-row">
        <span class="drag-handle">⠿</span>
        <select class="map-select" data-field="${escHtml(key)}" onchange="IS.setMapping(this.dataset.field, this.value)">${opts}</select>
        <span class="map-arrow">→</span>
        <div class="map-field-label">${escHtml(label)}${required ? ' <span style="color:var(--error)">*</span>' : ''}</div>
        <span class="map-ok">${val ? '✓' : ''}</span>
      </div>`;
    }).join('');

    const centerPanel = `<div class="panel">
      ${renderProfileToolbar()}
      <div class="map-header">
        <span></span>
        <div class="map-header-label" style="grid-column:2">소스 필드 (Excel)</div>
        <span></span>
        <div class="map-header-label" style="grid-column:4">대상 필드 (QA-Native)</div>
        <span></span>
      </div>
      <div class="mapping-list">${mapRows}</div>
      <div class="map-hint">⠿ 필드를 드래그하여 순서를 변경할 수 있습니다</div>
      ${renderSourceOverrides(excelColumns)}
    </div>`;

    // 오른쪽 패널: KPI + 미니 미리보기
    const summary = state.previewResult?.summary ?? {};
    const miniRows = (state.previewResult?.rows || []).slice(0, 5);
    const totalRows = (state.previewResult?.rows || []).length;

    const STATUS_LABEL = { added: '추가', updated: '업데이트', conflict: '충돌', error: '오류', same: '동일' };
    const STATUS_CLS   = { added: 'status-added', updated: 'status-updated', conflict: 'status-conflict', error: 'status-error', same: 'status-same' };

    const kpiHtml = [
      { label: '추가',     color: 'var(--add)',      val: summary.added    ?? 0 },
      { label: '업데이트', color: 'var(--update)',   val: summary.updated  ?? 0 },
      { label: '충돌',     color: 'var(--conflict)', val: summary.conflict ?? 0 },
      { label: '오류',     color: 'var(--error)',    val: summary.error    ?? 0 },
    ].map(({ label, color, val }) => `<div class="kpi-card">
      <div class="kpi-head"><div class="kpi-dot" style="background:${color}"></div><div class="kpi-label">${label}</div></div>
      <div class="kpi-num" style="color:${color}">${val}</div>
    </div>`).join('');

    const miniTableBody = miniRows.length
      ? miniRows.map((row) => `<tr>
            <td>${escHtml(row.tc_id ?? '')}</td>
            <td>${escHtml(row.title ?? '')}</td>
            <td>${escHtml(String(row.source_row ?? row.row ?? ''))}</td>
            <td><span class="status-pill ${STATUS_CLS[row.status] || ''}">${STATUS_LABEL[row.status] ?? escHtml(row.status)}</span></td>
          </tr>`).join('')
      : `<tr><td colspan="4" style="color:var(--text3);padding:10px 6px;text-align:center">미리보기 생성 후 확인 가능합니다</td></tr>`;

    const rightPanel = `<div class="panel">
      <div class="panel-header"><div class="panel-title">검증 결과</div></div>
      <div class="panel-body">
        <div class="kpi-grid">${kpiHtml}</div>
        <div class="preview-header">
          <div class="preview-label">미리보기 (상위 5개)</div>
          ${totalRows ? `<div class="preview-count">총 ${totalRows}개 행</div>` : ''}
          <button class="preview-btn" onclick="IS.next()">전체 미리보기</button>
        </div>
        <table class="mini-table">
          <thead><tr><th>test_id</th><th>title</th><th>행</th><th>상태</th></tr></thead>
          <tbody>${miniTableBody}</tbody>
        </table>
        <div class="legend">
          <div class="legend-item"><div class="legend-dot" style="background:var(--add)"></div>추가: 새로운 데이터</div>
          <div class="legend-item"><div class="legend-dot" style="background:var(--update)"></div>업데이트: 기존 변경</div>
          <div class="legend-item"><div class="legend-dot" style="background:var(--conflict)"></div>충돌: 중복/충돌</div>
          <div class="legend-item"><div class="legend-dot" style="background:var(--error)"></div>오류: 유효성 오류</div>
        </div>
      </div>
    </div>`;

    return `<div class="content" style="padding-bottom:0;overflow:hidden;display:flex;flex-direction:column;flex:1">
      <div class="step2-layout" style="flex:1;overflow:hidden">
        ${leftPanel}
        ${centerPanel}
        ${rightPanel}
      </div>
    </div>
    <div class="bottom-bar">
      ${SAFE_NOTE_HTML}
      <div class="spacer"></div>
      <button class="btn btn-ghost" onclick="IS.prev()">← 이전</button>
      <button class="btn btn-primary" data-testid="next-button" onclick="IS.next()" ${canGo ? '' : 'disabled'}>미리보기 생성 →</button>
    </div>`;
  }

  function getSelectedSheetSources() {
    return state.selectedSources.flatMap((source) => source.sheets.map((sheet) => ({
      fileId: source.fileId,
      sheet,
      key: `${source.fileId}::${sheet}`,
      fileName: state.files.find((file) => file.id === source.fileId)?.name || source.fileId,
    })));
  }

  function renderSourceOverrides(excelColumns) {
    const sources = getSelectedSheetSources();
    if (sources.length < 1) return '';
    if (!state.activeMappingSource || !sources.some((source) => source.key === state.activeMappingSource)) {
      state.activeMappingSource = sources[0].key;
    }
    const override = state.sourceMappings[state.activeMappingSource] || {};
    return `<div class="source-overrides">
      <div class="source-overrides-title">파일·시트별 예외 매핑 <span style="font-size:10px;color:var(--text3);margin-left:4px">공통 매핑과 다른 열만 지정하세요</span></div>
      <select class="override-select" onchange="IS.selectMappingSource(this.value)">
        ${sources.map((source) => `<option value="${escHtml(source.key)}" ${source.key === state.activeMappingSource ? 'selected' : ''}>${escHtml(source.fileName)} / ${escHtml(source.sheet)}</option>`).join('')}
      </select>
      <div class="override-grid">
        ${TC_FIELDS.map(({ key, label }) => `<label>${escHtml(label)}
          <select data-source-field="${escHtml(key)}" onchange="IS.setSourceMapping(this.dataset.sourceField, this.value)">
            ${['', ...excelColumns].map((col) => `<option value="${escHtml(col)}" ${override[key] === col ? 'selected' : ''}>${col ? escHtml(col) : `공통값 (${escHtml(state.mappings[key] || '없음')})`}</option>`).join('')}
          </select>
        </label>`).join('')}
      </div>
    </div>`;
  }

  function renderProfileToolbar() {
    const profileOpts = state.profiles.length
      ? state.profiles.map((p) =>
          `<option value="${escHtml(p.id)}">${escHtml(p.name)}</option>`
        ).join('')
      : '';

    return `<div class="profile-bar">
      <select class="profile-select" id="is-profile-select">
        <option value="">프로필 선택…</option>
        ${profileOpts}
      </select>
      ${state.profiles.length ? `<button class="btn-sm" onclick="IS.loadProfile()">불러오기</button>` : ''}
      <button class="btn-sm" data-testid="save-profile-button" onclick="IS.saveProfile()">💾 저장</button>
      ${state.profiles.map((p) => `
        <button class="btn-sm" style="color:var(--error);border-color:rgba(248,113,113,.3)"
                onclick="IS.deleteProfile('${escHtml(p.id)}')" title="${escHtml(p.name)} 삭제">🗑 ${escHtml(p.name)}</button>
      `).join('')}
    </div>`;
  }

  // ─────────────────────────────────────────
  // Step 3: 미리보기
  // ─────────────────────────────────────────
  function renderStep3() {
    if (state.loading) {
      return `<div class="content" style="display:flex;align-items:center;justify-content:center;flex:1">
        <div style="text-align:center">
          <div class="spinner"></div>
          <p style="margin-top:16px;color:var(--text2)">미리보기 생성 중...</p>
        </div>
      </div>`;
    }

    if (!state.previewResult) {
      return `<div class="content">
        <p style="color:var(--error);margin-bottom:12px">미리보기 생성에 실패했습니다.</p>
        <button class="btn btn-ghost" onclick="IS.prev()">← 이전 단계로</button>
      </div>
      <div class="bottom-bar">
        ${SAFE_NOTE_HTML}
        <div class="spacer"></div>
        <button class="btn btn-ghost" onclick="IS.prev()">← 이전</button>
      </div>`;
    }

    const { summary = {}, rows = [] } = state.previewResult;
    const canGo = validators[3](state);
    const unresolved = unresolvedConflictCount();
    const totalCounts = {
      all: rows.length,
      added: rows.filter((r) => r.status === 'added').length,
      updated: rows.filter((r) => r.status === 'updated').length,
      conflict: rows.filter((r) => r.status === 'conflict').length,
      error: rows.filter((r) => r.status === 'error').length,
      same: rows.filter((r) => r.status === 'same').length,
    };

    const filterBtns = [
      { key: 'all',      cls: 'f-all', label: `전체 ${totalCounts.all}` },
      { key: 'added',    cls: 'f-add', label: `추가 ${totalCounts.added}` },
      { key: 'updated',  cls: 'f-upd', label: `업데이트 ${totalCounts.updated}` },
      { key: 'conflict', cls: 'f-con', label: `충돌 ${totalCounts.conflict}` },
      { key: 'error',    cls: 'f-err', label: `오류 ${totalCounts.error}` },
      { key: 'same',     cls: 'f-sam', label: `동일 ${totalCounts.same}` },
    ].map(({ key, cls, label }) =>
      `<button class="filter-btn ${cls}${state.activeFilter === key ? ' active' : ''}" onclick="IS.setFilter('${key}')">${label}</button>`
    ).join('');

    return `<div class="content">
      ${totalCounts.conflict > 0 ? `<div style="background:var(--conflict-bg);border:1px solid rgba(251,191,36,.3);border-radius:8px;padding:10px 14px;margin-bottom:12px;font-size:12px;color:var(--conflict);display:flex;align-items:center;gap:8px">
        <span>⚠</span>
        충돌 ${totalCounts.conflict}건이 있습니다. 다음 단계에서 반영 정책을 선택하면 자동으로 처리됩니다.
      </div>` : ''}
      <div class="preview-filters">${filterBtns}</div>
      <div class="full-table-wrap" data-testid="preview-table">
        ${renderPreviewTable(rows)}
      </div>
    </div>
    <div class="bottom-bar">
      ${SAFE_NOTE_HTML}
      <div class="spacer"></div>
      <button class="btn btn-ghost" onclick="IS.prev()">← 이전</button>
      <button class="btn btn-primary" data-testid="next-button" onclick="IS.next()">안전한 반영 →</button>
    </div>`;
  }

  // renderSummaryCards 유지 (하위 호환)
  function renderSummaryCards(summary) {
    return '';
  }

  function renderPreviewTable(rows) {
    const filtered = state.activeFilter === 'all'
      ? rows
      : rows.filter((r) => r.status === state.activeFilter);

    if (!filtered.length) {
      return `<p style="color:var(--text3);padding:40px;text-align:center">해당 상태의 데이터가 없습니다.</p>`;
    }

    const STATUS_LABEL = { added: '추가', updated: '업데이트', conflict: '충돌', error: '오류', same: '동일' };
    const STATUS_CLS   = { added: 'status-added', updated: 'status-updated', conflict: 'status-conflict', error: 'status-error', same: 'status-same' };

    const tbody = filtered.map((row) => {
      const key = rowKey(row);
      const decision = state.decisions[key];
      // precondition/steps/expected 는 after(또는 before) 안에 있을 수 있음
      const detail = row.after || row.before || {};
      const precondition = row.precondition ?? detail.precondition ?? '';
      const steps       = row.steps       ?? detail.steps       ?? '';
      const expected    = row.expected    ?? detail.expected    ?? '';
      return `<tr data-status="${escHtml(row.status)}" data-row-key="${escHtml(key)}" ${decision ? 'data-decision="exclude"' : ''}>
        <td>${escHtml(row.tc_id ?? '')}</td>
        <td>${escHtml(row.title ?? '')}</td>
        <td style="max-width:200px;white-space:pre-wrap;overflow-wrap:break-word;word-break:break-word">${escHtml(precondition)}</td>
        <td style="max-width:200px;white-space:pre-wrap;overflow-wrap:break-word;word-break:break-word">${escHtml(steps)}</td>
        <td style="max-width:200px;white-space:pre-wrap;overflow-wrap:break-word;word-break:break-word">${escHtml(expected)}</td>
        <td>${escHtml(row.group ?? '')}</td>
        <td><span class="status-pill ${STATUS_CLS[row.status] || ''}">${STATUS_LABEL[row.status] ?? escHtml(row.status)}</span></td>
      </tr>`;
    }).join('');

    return `<table class="full-table">
      <colgroup>
        <col style="width:80px">
        <col style="width:160px">
        <col style="width:200px">
        <col style="width:200px">
        <col style="width:220px">
        <col style="width:110px">
        <col style="width:60px">
      </colgroup>
      <thead>
        <tr>
          <th>TC ID</th><th>제목</th><th>전제조건</th><th>테스트 단계</th><th>기대결과</th><th>그룹</th><th>상태</th>
        </tr>
      </thead>
      <tbody>${tbody}</tbody>
    </table>`;
  }

  // ─────────────────────────────────────────
  // Step 4: 안전한 반영
  // ─────────────────────────────────────────
  function renderStep4() {
    const summary = state.previewResult?.summary ?? {};
    const rows = state.previewResult?.rows || [];
    const groups = [...new Set(rows.map((r) => r.group).filter(Boolean))];

    const policies = [
      { key: 'skip-conflict',         badge: 'rec',    badgeLabel: '권장', name: 'skip-conflict',         desc: '추가·업데이트만 반영. 충돌 항목은 자동으로 건너뛰고 CSV 다운로드로 수동 검토할 수 있습니다.' },
      { key: 'overwrite',             badge: 'warn',   badgeLabel: '주의', name: 'overwrite',             desc: '충돌 항목도 Excel 데이터로 덮어씁니다. 기존 내용이 사라지므로 스냅샷을 꼭 확인하세요.' },
      { key: 'replace-with-snapshot', badge: 'danger', badgeLabel: '위험', name: 'replace-with-snapshot', desc: '대상 그룹 전체를 교체합니다. 기존 파일이 모두 삭제되며 스냅샷으로만 복구 가능합니다.' },
    ];

    const policyCards = policies.map(({ key, badge, badgeLabel, name, desc }) =>
      `<div class="policy-card${state.policy === key ? ' selected' : ''}" onclick="IS.selectPolicy('${key}')">
        <div class="policy-badge ${badge}">${badgeLabel}</div>
        <div class="policy-name">${name}</div>
        <div class="policy-desc">${desc}</div>
      </div>`
    ).join('');

    const conflictLabel = state.policy === 'overwrite' ? '충돌 (덮어씀)' : '충돌 (스킵)';

    return `<div class="content">
      <p style="font-size:13px;color:var(--text2);margin-bottom:16px">반영 정책을 선택하고 최종 확인 후 안전하게 반영합니다. 모든 변경 전에 스냅샷이 자동 생성됩니다.</p>
      <div class="policy-grid">${policyCards}</div>
      <div class="commit-summary">
        <h3>반영 요약</h3>
        ${groups.length ? `<div class="commit-row"><span class="commit-label">반영 대상 그룹</span><span style="color:var(--accent);font-weight:600">${escHtml(groups.join(', '))}</span></div>` : ''}
        <div class="commit-row"><span class="commit-label">새로 추가</span><span style="color:var(--add);font-weight:600">${summary.added ?? 0}개</span></div>
        <div class="commit-row"><span class="commit-label">업데이트</span><span style="color:var(--update);font-weight:600">${summary.updated ?? 0}개</span></div>
        <div class="commit-row"><span class="commit-label">${conflictLabel}</span><span style="color:var(--conflict);font-weight:600">${summary.conflict ?? 0}개 → 건너뜀</span></div>
        <div class="commit-row"><span class="commit-label">오류</span><span style="color:var(--error);font-weight:600">${summary.error ?? 0}개 → 건너뜀</span></div>
      </div>
      <div class="snapshot-info">
        <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor" style="color:var(--accent);flex-shrink:0"><path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/></svg>
        반영 직전 <strong style="color:var(--text);margin:0 4px">자동 스냅샷</strong>이 생성됩니다. 문제가 생기면 1클릭으로 롤백할 수 있습니다.
      </div>
      ${state.error ? `<p style="color:var(--error);margin-top:12px;font-size:12px">${escHtml(state.error)}</p>` : ''}
    </div>
    <div class="bottom-bar">
      ${SAFE_NOTE_HTML}
      <div class="spacer"></div>
      <button class="btn btn-ghost" onclick="IS.prev()">← 이전</button>
      <button class="btn btn-success" data-testid="commit-button" onclick="IS.commit()" ${state.loading ? 'disabled' : ''}>
        ${state.loading ? '처리 중...' : '✓ 반영 시작'}
      </button>
    </div>`;
  }

  // ─────────────────────────────────────────
  // Step 5: 완료
  // ─────────────────────────────────────────
  function renderStep5() {
    const cr = state.commitResult ?? {};
    const rolledBack = state.rollbackResult?.status === 'rolled_back';
    const rows = state.previewResult?.rows || [];
    const groups = [...new Set(rows.map((r) => r.group).filter(Boolean))];
    const summary = state.previewResult?.summary ?? {};

    const snapshotId = cr.snapshot_id || state.runId || '';
    const snapshotShort = snapshotId.slice(0, 20) || '—';
    const total = cr.committed ?? 0;

    if (rolledBack) {
      return `<div class="content">
        <div class="result-hero">
          <div class="result-icon">↩</div>
          <div class="result-title">롤백 완료</div>
          <div class="result-sub">모든 변경 사항이 원래 상태로 복원되었습니다.</div>
          <div class="result-actions">
            <button class="btn btn-primary" data-testid="new-import-button" onclick="IS.startNewImport()">새 가져오기</button>
          </div>
        </div>
      </div>`;
    }

    const groupChips = groups.map((g) => `<span class="group-chip">📁 ${escHtml(g)}</span>`).join('');

    return `<div class="content">
      <div class="result-hero">
        <div class="result-icon">✅</div>
        <div class="result-title">${total}개 테스트케이스가 반영되었습니다</div>
        ${snapshotId ? `<div class="result-sub">스냅샷 <code style="background:var(--card2);padding:2px 6px;border-radius:4px;font-family:monospace;font-size:11px">${escHtml(snapshotShort)}</code> 생성 완료</div>` : ''}
        <div class="result-stats">
          <div class="result-stat"><div class="result-stat-num" style="color:var(--add)">${summary.added ?? 0}</div><div class="result-stat-label">추가</div></div>
          <div class="result-stat"><div class="result-stat-num" style="color:var(--update)">${summary.updated ?? 0}</div><div class="result-stat-label">업데이트</div></div>
          <div class="result-stat"><div class="result-stat-num" style="color:var(--conflict)">${summary.conflict ?? 0}</div><div class="result-stat-label">스킵(충돌)</div></div>
          <div class="result-stat"><div class="result-stat-num" style="color:var(--error)">${summary.error ?? 0}</div><div class="result-stat-label">스킵(오류)</div></div>
        </div>
        <div class="result-actions">
          ${state.runId ? `<button class="btn btn-ghost" onclick="IS.downloadCsv()">📥 오류 목록 다운로드</button>` : ''}
          ${state.runId ? `<button class="btn btn-ghost" data-testid="rollback-button" onclick="IS.rollback()" ${state.loading ? 'disabled' : ''}>↩ 전체 롤백</button>` : ''}
          <button class="btn btn-primary" data-testid="new-import-button" onclick="IS.startNewImport()">새 가져오기</button>
        </div>
      </div>
      ${groups.length ? `
        <div class="result-groups" style="margin-top:16px">
          <h3>반영된 그룹</h3>
          <div style="margin-top:8px">${groupChips}</div>
        </div>
      ` : ''}
      ${state.runId ? `<div style="margin-top:16px;padding-bottom:20px"><span class="rollback-link" onclick="IS.rollback()">↩ 이전 스냅샷으로 롤백</span></div>` : ''}
    </div>`;
  }

  function renderModal() {
    if (!state.modal) return '';
    const modal = state.modal;
    const isInput = modal.type === 'input';
    const dangerBtn = modal.danger ? 'style="background:var(--error);color:#fff"' : '';
    return `<div class="modal-backdrop" role="presentation" onclick="if(event.target===this)IS.cancelModal()" onkeydown="IS.handleModalKeydown(event)">
      <section class="modal" role="dialog" aria-modal="true" aria-labelledby="is-modal-title">
        <h3 id="is-modal-title">${escHtml(modal.title)}</h3>
        <p>${escHtml(modal.message || '')}</p>
        ${isInput ? `<input id="is-modal-input" class="modal-input" placeholder="프로필 이름" value="${escHtml(modal.value || '')}"
                 onkeydown="if(event.key==='Enter')IS.submitModal(this.value);if(event.key==='Escape')IS.cancelModal()">` : ''}
        ${modal.validationError ? `<p class="modal-error" role="alert">${escHtml(modal.validationError)}</p>` : ''}
        <div class="modal-actions">
          <button class="btn btn-ghost" onclick="IS.cancelModal()">취소</button>
          <button class="btn btn-primary" ${dangerBtn}
                  onclick="IS.submitModal(${isInput ? "document.getElementById('is-modal-input').value" : ''})">${escHtml(modal.confirmLabel || '확인')}</button>
        </div>
      </section>
    </div>`;
  }

  // ─────────────────────────────────────────
  // 이벤트 핸들러 (전역 IS.xxx() 노출)
  // ─────────────────────────────────────────

  /** 파일 선택 — 다중 선택. 선택된 파일은 적어도 한 시트를 골라야 한다. */
  function selectFile(fileId) {
    const file = state.files.find((f) => f.id === fileId);
    if (!file) return;
    if (file.error || !Array.isArray(file.sheets) || !file.sheets.length) return;
    const index = state.selectedSources.findIndex((source) => source.fileId === fileId);
    if (index >= 0) {
      state.selectedSources.splice(index, 1);
      Object.keys(state.sourceMappings).forEach((key) => {
        if (key.startsWith(`${fileId}::`)) delete state.sourceMappings[key];
      });
    } else {
      state.selectedSources.push({ fileId, sheets: [] });
    }
    render();
  }

  /** 파일별 시트 체크박스 토글 */
  function toggleSheet(fileId, sheetName) {
    const source = state.selectedSources.find((item) => item.fileId === fileId);
    if (!source) return;
    const idx = source.sheets.indexOf(sheetName);
    if (idx >= 0) {
      source.sheets.splice(idx, 1);
      delete state.sourceMappings[`${fileId}::${sheetName}`];
    } else {
      source.sheets.push(sheetName);
    }
    render();
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

  function selectMappingSource(sourceKey) {
    state.activeMappingSource = sourceKey;
    render();
  }

  function setSourceMapping(field, col) {
    if (!state.activeMappingSource) return;
    const mappings = state.sourceMappings[state.activeMappingSource] || {};
    if (col) mappings[field] = col;
    else delete mappings[field];
    if (Object.keys(mappings).length) state.sourceMappings[state.activeMappingSource] = mappings;
    else delete state.sourceMappings[state.activeMappingSource];
  }

  function toggleConflictDecision(key) {
    if (state.decisions[key] === 'exclude') delete state.decisions[key];
    else state.decisions[key] = 'exclude';
    render();
  }

  function captureFocusToken() {
    const active = document.activeElement;
    if (!(active instanceof Element)) return null;
    if (active.id) return { type: 'id', value: active.id };
    if (active.dataset.testid) return { type: 'testid', value: active.dataset.testid };
    const profileItem = active.closest('.is-profile-item');
    if (profileItem?.dataset.profileId) {
      return { type: 'profile-delete', value: profileItem.dataset.profileId };
    }
    return null;
  }

  function findFocusTarget(token) {
    if (!token) return null;
    let target = null;
    if (token.type === 'id') target = document.getElementById(token.value);
    if (token.type === 'testid') {
      target = [...document.querySelectorAll('[data-testid]')]
        .find((element) => element.dataset.testid === token.value) || null;
    }
    if (token.type === 'profile-delete') {
      target = [...document.querySelectorAll('.is-profile-item')]
        .find((element) => element.dataset.profileId === token.value)
        ?.querySelector('.is-profile-delete-btn') || null;
    }
    return target;
  }

  function restoreFocus(token, fallbackToken = null) {
    const target = findFocusTarget(token) || findFocusTarget(fallbackToken);
    target?.focus();
  }

  function modalFocusables() {
    const modal = document.querySelector('.modal');
    if (!modal) return [];
    return [...modal.querySelectorAll(
      'button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])'
    )];
  }

  function handleModalKeydown(event) {
    if (!state.modal) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      cancelModal();
      return;
    }
    if (event.key !== 'Tab') return;
    const focusables = modalFocusables();
    if (!focusables.length) {
      event.preventDefault();
      return;
    }
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (event.shiftKey && (document.activeElement === first || !focusables.includes(document.activeElement))) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !focusables.includes(document.activeElement))) {
      event.preventDefault();
      first.focus();
    }
  }

  function openModal(modal) {
    state.modal = { ...modal, focusToken: captureFocusToken() };
    render().then(() => {
      const target = document.getElementById('is-modal-input') || document.querySelector('.modal .btn-primary, .modal .btn-ghost');
      target?.focus();
    });
  }

  function cancelModal() {
    const focusToken = state.modal?.focusToken;
    state.modal = null;
    render().then(() => restoreFocus(focusToken));
  }

  async function submitModal(value) {
    const modal = state.modal;
    if (!modal) return;
    if (modal.type === 'input' && !String(value || '').trim()) {
      state.modal = { ...modal, validationError: '프로필 이름을 입력하세요.' };
      await render();
      document.getElementById('is-modal-input')?.focus();
      return;
    }
    const focusToken = modal.focusToken;
    state.modal = null;
    await render();
    await modal.action(value);
    restoreFocus(focusToken, modal.successFocusToken);
  }

  /** 프로필 저장 */
  function saveProfile() {
    openModal({
      type: 'input',
      title: '매핑 프로필 저장',
      message: '현재 공통 열 매핑을 다시 사용할 이름으로 저장합니다.',
      confirmLabel: '저장',
      action: _saveProfile,
    });
  }

  async function _saveProfile(name) {
    try {
      await callApi('POST', '/api/import/profiles', { name: name.trim(), mappings: state.mappings });
      const data = await callApi('GET', '/api/import/profiles');
      state.profiles = data.profiles || [];
      await render();
    } catch (err) {
      state.error = errorMessage(err, '프로필 저장에 실패했습니다.');
      await render();
    }
  }

  /** 프로필 삭제 */
  function deleteProfile(profileId) {
    const profile = state.profiles.find((p) => p.id === profileId);
    const name = profile ? profile.name : profileId;
    openModal({
      type: 'confirm',
      title: '매핑 프로필 삭제',
      message: `"${name}" 프로필을 삭제하시겠습니까?`,
      confirmLabel: '삭제',
      danger: true,
      successFocusToken: { type: 'testid', value: 'save-profile-button' },
      action: () => _deleteProfile(profileId),
    });
  }

  async function _deleteProfile(profileId) {
    try {
      await callApi('DELETE', `/api/import/profiles/${encodeURIComponent(profileId)}`);
      const data = await callApi('GET', '/api/import/profiles');
      state.profiles = data.profiles || [];
      await render();
    } catch (err) {
      state.error = errorMessage(err, '프로필 삭제에 실패했습니다.');
      await render();
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

  /** Step4 정책 선택 */
  function selectPolicy(policyKey) {
    state.policy = policyKey;
    render();
  }

  /** Step3 필터 변경 */
  function setFilter(status) {
    state.activeFilter = status;
    render();
  }

  /** 초기화 재시도 */
  async function retryInit() {
    state.files = [];
    state.error = null;
    await render();
  }

  /** CSV 다운로드 */
  function downloadCsv() {
    if (!state.runId) return;
    window.location.href = `/api/import/runs/${encodeURIComponent(state.runId)}/skipped.csv`;
  }

  /** 커밋 실행 — 하나의 run_id를 한 번만 커밋한다. */
  async function commit() {
    if (state.loading) return;
    state.loading = true;
    state.error = null;
    await render();
    try {
      if (!state.runId) throw new Error('run_id가 없습니다.');
      // 충돌은 Step4 정책(skip-conflict/overwrite/replace-with-snapshot)으로 일괄 처리 — 여기서 차단하지 않음
      if (!state.idempotencyKey) state.idempotencyKey = makeIdempotencyKey(state.runId);
      const decisions = (state.previewResult?.rows || [])
        .filter((row) => state.decisions[rowKey(row)] === 'exclude')
        .map((row) => ({
          file_id: row.source_file_id || row.file_id,
          file_name: row.file_name || row.source_file || '',
          sheet_name: row.sheet_name || row.source_sheet || '',
          source_row: row.source_row ?? row.row,
          tc_id: row.tc_id || '',
          action: 'exclude',
        }));
      let commitResponse;
      let reconcilingAlreadyCommitted = false;
      try {
        commitResponse = await callApi('POST', '/api/import/commit', {
          run_id: state.runId,
          idempotency_key: state.idempotencyKey,
          policy: state.policy || 'skip-conflict',
          decisions,
        });
      } catch (err) {
        if (err?.code !== 'ALREADY_COMMITTED') throw err;
        reconcilingAlreadyCommitted = true;
        commitResponse = { status: 'committed', reconciled: true };
      }
      if (commitResponse.status !== 'committed') {
        throw new Error('서버가 커밋 완료 상태를 반환하지 않았습니다.');
      }
      const run = await callApi('GET', `/api/import/runs/${encodeURIComponent(state.runId)}`);
      if (run.status !== 'committed') {
        throw new Error(`커밋 최종 상태가 올바르지 않습니다: ${run.status || '알 수 없음'}`);
      }
      if (reconcilingAlreadyCommitted && run.idempotency_key !== state.idempotencyKey) {
        const conflict = new Error('이미 다른 요청으로 커밋된 작업입니다. 현재 요청을 완료로 처리하지 않았습니다.');
        conflict.code = 'IDEMPOTENCY_CONFLICT';
        throw conflict;
      }
      state.commitResult = {
        ...commitResponse,
        ...run,
        committed: run.committed ?? run.result?.committed ?? 0,
        skipped: run.skipped ?? run.result?.skipped ?? 0,
      };
      state.loading = false;
      goTo(5);
      _playConfetti();
    } catch (err) {
      state.error = errorMessage(err, '커밋에 실패했습니다. 다시 시도하세요.');
      state.loading = false;
      await render();
    }
  }

  /** 롤백 실행 */
  function rollback() {
    if (!state.runId) return;
    openModal({
      type: 'confirm',
      title: '전체 작업 롤백',
      message: '이 가져오기 작업으로 반영한 모든 변경을 원래 상태로 복원합니다.',
      confirmLabel: '전체 롤백',
      danger: true,
      successFocusToken: { type: 'testid', value: 'new-import-button' },
      action: _rollback,
    });
  }

  async function _rollback() {
    if (!state.runId || state.loading) return;
    state.loading = true;
    state.error = null;
    await render();
    try {
      const rollbackResult = await callApi('POST', `/api/import/runs/${encodeURIComponent(state.runId)}/rollback`, {});
      const run = await callApi('GET', `/api/import/runs/${encodeURIComponent(state.runId)}`);
      if (rollbackResult.status !== 'rolled_back' || run.status !== 'rolled_back') {
        throw new Error(`롤백 최종 상태가 올바르지 않습니다: ${run.status || rollbackResult.status || '알 수 없음'}`);
      }
      state.rollbackResult = {
        ...rollbackResult,
        ...run,
        status: 'rolled_back',
        verified: rollbackResult.verified ?? run.rollback_result?.verified ?? false,
      };
      state.loading = false;
      await render();
    } catch (err) {
      state.loading = false;
      state.error = errorMessage(err, '롤백에 실패했습니다.');
      await render();
    }
  }

  function startNewImport() {
    state.step = 1;
    state.selectedSources = [];
    state.mappings = {};
    state.sourceMappings = {};
    state.activeMappingSource = '';
    state.previewResult = null;
    state.runId = null;
    state.idempotencyKey = null;
    state.commitResult = null;
    state.rollbackResult = null;
    state.decisions = {};
    state.error = null;
    state.activeFilter = 'all';
    state.policy = 'skip-conflict';
    render();
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

  /** 미리보기 API 호출 — 모든 파일/시트를 하나의 원자적 run으로 생성 */
  async function _loadPreview() {
    state.loading = true;
    state.previewResult = null;
    state.error = null;
    state.runId = null;
    state.idempotencyKey = null;
    state.commitResult = null;
    state.rollbackResult = null;
    state.decisions = {};
    await render();
    try {
      const sources = getSelectedSheetSources().map((source) => ({
        file_id: source.fileId,
        sheet_name: source.sheet,
        mappings: { ...state.mappings, ...(state.sourceMappings[source.key] || {}) },
      }));
      const result = await callApi('POST', '/api/import/preview', {
        sources,
        mappings: state.mappings,
      });
      state.previewResult = result;
      state.runId = result.run_id || null;
      state.idempotencyKey = state.runId ? makeIdempotencyKey(state.runId) : null;
      if (!state.runId) throw new Error('미리보기 응답에 run_id가 없습니다.');
    } catch (err) {
      state.error = err.error || err.message || '미리보기 생성에 실패했습니다.';
    } finally {
      state.loading = false;
    }
    if (!state.previewResult) await render();
  }

  /** 다음 버튼 활성/비활성 갱신 (DOM 직접 조작, 전체 재렌더 방지) */
  function _updateNavButtons() {
    // 버튼들은 data-testid="next-button" / "commit-button" 으로 찾기
    const nextBtn = document.querySelector('[data-testid="next-button"]');
    if (!nextBtn) return;
    if (canNext()) {
      nextBtn.removeAttribute('disabled');
      nextBtn.removeAttribute('aria-disabled');
    } else {
      nextBtn.setAttribute('disabled', '');
      nextBtn.setAttribute('aria-disabled', 'true');
    }
  }

  /** 컨페티 완료 애니메이션 */
  function _playConfetti() {
    const colors = ['#8B5CF6', '#22C55E', '#3B82F6', '#F59E0B', '#EF4444', '#EC4899'];
    for (let i = 0; i < 60; i++) {
      const el = document.createElement('div');
      el.className = 'is-confetti-piece'; // 전역 keyframe 유지
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
  let _renderPromise = null;
  async function render() {
    if (_renderPromise) return _renderPromise;
    _renderPromise = new Promise((resolve) => {
      _renderRaf = requestAnimationFrame(async () => {
        try {
          await _doRender();
        } finally {
          _renderRaf = null;
          _renderPromise = null;
          resolve();
        }
      });
    });
    return _renderPromise;
  }

  async function _doRender() {
    const container = document.getElementById('import-studio-root');
    if (!container) return;

    // 컨테이너에 .import-studio 클래스 적용 (단 한 번이면 충분하지만 idempotent)
    container.classList.add('import-studio');

    // Step 콘텐츠 생성 (Step1만 async)
    let stepInnerHtml = '';
    switch (state.step) {
      case 1: stepInnerHtml = await renderStep1(); break;
      case 2: stepInnerHtml = renderStep2();       break;
      case 3: stepInnerHtml = renderStep3();       break;
      case 4: stepInnerHtml = renderStep4();       break;
      case 5: stepInnerHtml = renderStep5();       break;
      default: stepInnerHtml = '';
    }

    // 에러 배너 (Step4는 내부에서 처리)
    const errorBanner = state.error && state.step !== 4
      ? `<div class="error-banner" role="alert">${escHtml(state.error)}</div>`
      : '';

    const liveStatus = state.error
      ? `오류: ${state.error}`
      : state.loading ? '처리 중입니다.'
      : `가져오기 ${state.step}단계`;

    container.innerHTML = `
      <div class="sr-only" role="status" aria-live="polite">${escHtml(liveStatus)}</div>
      <div class="page-header">
        <div class="page-title">Excel Import Studio</div>
        <div class="wizard">${renderWizardHeader()}</div>
        ${state.step > 1 ? `<button class="btn btn-ghost reset-btn" onclick="IS.startNewImport()" title="처음부터 다시 시작">↺ 리셋</button>` : ''}
      </div>
      ${errorBanner}
      <div class="step-content active" aria-busy="${state.loading}">
        ${stepInnerHtml}
      </div>
      ${renderModal()}
    `;
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
    el.classList.add('import-studio'); // 아티팩트 스코프 클래스

    // 매핑 프로필 사전 로드
    try {
      const data = await callApi('GET', '/api/import/profiles');
      state.profiles = data.profiles || [];
    } catch (err) {
      state.profiles = [];
      state.error = errorMessage(err, '매핑 프로필을 불러오지 못했습니다. 서버 연결을 확인하세요.');
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
    selectMappingSource,
    setSourceMapping,
    toggleConflictDecision,
    saveProfile,
    loadProfile,
    deleteProfile,
    // Step3
    downloadCsv,
    setFilter,
    // Step4
    commit,
    selectPolicy,
    // Step5
    rollback,
    startNewImport,
    cancelModal,
    submitModal,
    handleModalKeydown,
  };
})();

window.IS = IS;
