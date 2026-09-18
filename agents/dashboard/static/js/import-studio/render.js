// Import Studio — 5단계 위저드 화면 템플릿 (순수 렌더링, state를 읽기만 함)
// onclick="IS.xxx()" 문자열은 window.IS(전역)를 참조하므로 handlers.js가 로드되기 전에도 문제 없다.
(function (NS) {
  'use strict';

  const { state, validators, TC_FIELDS } = NS;
  const {
    escHtml,
    getExcelColumns,
    formatSize,
    formatDate,
    rowKey,
    unresolvedConflictCount,
    getSelectedSheetSources,
  } = NS;
  const { callApi } = NS;

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
            return `<div class="sheet-row"
                        onclick="event.stopPropagation();IS.toggleSheet('${escHtml(file.id)}','${escHtml(sheetName)}')"
                        role="checkbox" aria-checked="${checked}">
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

  // ─────────────────────────────────────────
  // Step 2: 열 매핑 (3열 레이아웃)
  // ─────────────────────────────────────────
  function renderStep2() {
    const excelColumns = getExcelColumns();
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

    // 오른쪽 패널: 이미지 기준 검증 결과 요약. 상세 행 미리보기는 다음 단계에서 제공한다.
    const summary = state.previewResult?.summary ?? {};
    const unchanged = summary.same ?? summary.unchanged ?? 0;
    const mappedFields = TC_FIELDS.filter(({ key }) => state.mappings[key]).length;
    const hasValidation = state.previewResult !== null;
    const panelBadge = hasValidation
      ? (summary.total ?? (summary.added ?? 0) + (summary.updated ?? 0) + (summary.conflict ?? 0) + (summary.error ?? 0) + unchanged)
      : `${mappedFields}/${TC_FIELDS.length}`;
    const rightPanel = `<div class="panel validation-panel">
      <div class="panel-header"><div class="panel-title">검증 결과</div><div class="panel-badge">${panelBadge}</div></div>
      <div class="panel-body">
        <div class="kpi-grid">
          <div class="kpi-card"><div class="kpi-head"><div class="kpi-dot" style="background:var(--add)"></div><div class="kpi-label">추가</div></div><div class="kpi-num" style="color:var(--add)">${summary.added ?? 0}</div></div>
          <div class="kpi-card"><div class="kpi-head"><div class="kpi-dot" style="background:var(--update)"></div><div class="kpi-label">업데이트</div></div><div class="kpi-num" style="color:var(--update)">${summary.updated ?? 0}</div></div>
          <div class="kpi-card"><div class="kpi-head"><div class="kpi-dot" style="background:var(--conflict)"></div><div class="kpi-label">충돌</div></div><div class="kpi-num" style="color:var(--conflict)">${summary.conflict ?? 0}</div></div>
          <div class="kpi-card"><div class="kpi-head"><div class="kpi-dot" style="background:var(--error)"></div><div class="kpi-label">오류</div></div><div class="kpi-num" style="color:var(--error)">${summary.error ?? 0}</div></div>
        </div>
        <div class="kpi-card kpi-card-wide"><div class="kpi-head"><div class="kpi-dot" style="background:var(--text3)"></div><div class="kpi-label">동일 · 변경 필요 없음</div></div><div class="kpi-num" style="color:var(--text2)">${unchanged}</div></div>
        <div class="validation-note">${hasValidation ? '상세 테스트 케이스는 다음 미리보기 단계에서 확인할 수 있습니다.' : `소스 필드 매핑 ${mappedFields}/${TC_FIELDS.length} 완료 · 모든 필수 필드를 선택하면 미리보기를 생성할 수 있습니다.`}</div>
        <div class="legend">
          <div class="legend-item"><div class="legend-dot" style="background:var(--add)"></div>추가</div>
          <div class="legend-item"><div class="legend-dot" style="background:var(--update)"></div>업데이트</div>
          <div class="legend-item"><div class="legend-dot" style="background:var(--conflict)"></div>충돌</div>
          <div class="legend-item"><div class="legend-dot" style="background:var(--error)"></div>오류</div>
          <div class="legend-item"><div class="legend-dot" style="background:var(--text3)"></div>동일</div>
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

    const { rows = [] } = state.previewResult;
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

  Object.assign(NS, {
    renderWizardHeader,
    renderStep1,
    renderStep2,
    renderStep3,
    renderStep4,
    renderStep5,
    renderModal,
  });
})(window.__importStudioNS = window.__importStudioNS || {});
