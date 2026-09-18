// Import Studio — 이벤트 핸들러 (전역 IS.xxx()로 노출되는 것들 + 내부 헬퍼)
// render()는 main.js(이 파일보다 나중에 로드됨)가 채우므로 NS.render(...)로
// 매 호출마다 동적으로 참조한다 (top-level에서 구조분해하면 undefined가 캡처됨).
(function (NS) {
  'use strict';

  const { state, validators, DEFAULT_MAPPINGS } = NS;
  const { callApi } = NS;
  const { errorMessage, rowKey, makeIdempotencyKey, getSelectedSheetSources } = NS;

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
    NS.render();
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
    NS.render();
  }

  /** 열 매핑 변경 — targeted DOM update */
  function setMapping(field, col) {
    if (col) {
      state.mappings[field] = col;
    } else {
      delete state.mappings[field];
    }
    state.previewResult = null;
    // 매핑 진행률과 검증 패널을 즉시 갱신한다.
    NS.render();
  }

  function selectMappingSource(sourceKey) {
    state.activeMappingSource = sourceKey;
    NS.render();
  }

  function setSourceMapping(field, col) {
    if (!state.activeMappingSource) return;
    const mappings = state.sourceMappings[state.activeMappingSource] || {};
    if (col) mappings[field] = col;
    else delete mappings[field];
    if (Object.keys(mappings).length) state.sourceMappings[state.activeMappingSource] = mappings;
    else delete state.sourceMappings[state.activeMappingSource];
    state.previewResult = null;
    NS.render();
  }

  function toggleConflictDecision(key) {
    if (state.decisions[key] === 'exclude') delete state.decisions[key];
    else state.decisions[key] = 'exclude';
    NS.render();
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
    NS.render().then(() => {
      const target = document.getElementById('is-modal-input') || document.querySelector('.modal .btn-primary, .modal .btn-ghost');
      target?.focus();
    });
  }

  function cancelModal() {
    const focusToken = state.modal?.focusToken;
    state.modal = null;
    NS.render().then(() => restoreFocus(focusToken));
  }

  async function submitModal(value) {
    const modal = state.modal;
    if (!modal) return;
    if (modal.type === 'input' && !String(value || '').trim()) {
      state.modal = { ...modal, validationError: '프로필 이름을 입력하세요.' };
      await NS.render();
      document.getElementById('is-modal-input')?.focus();
      return;
    }
    const focusToken = modal.focusToken;
    state.modal = null;
    await NS.render();
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
      await NS.render();
    } catch (err) {
      state.error = errorMessage(err, '프로필 저장에 실패했습니다.');
      await NS.render();
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
      await NS.render();
    } catch (err) {
      state.error = errorMessage(err, '프로필 삭제에 실패했습니다.');
      await NS.render();
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
      NS.render();
    }
  }

  /** Step4 정책 선택 */
  function selectPolicy(policyKey) {
    state.policy = policyKey;
    NS.render();
  }

  /** Step3 필터 변경 */
  function setFilter(status) {
    state.activeFilter = status;
    NS.render();
  }

  /** 초기화 재시도 */
  async function retryInit() {
    state.files = [];
    state.error = null;
    await NS.render();
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
    await NS.render();
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
      await NS.render();
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
    await NS.render();
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
      await NS.render();
    } catch (err) {
      state.loading = false;
      state.error = errorMessage(err, '롤백에 실패했습니다.');
      await NS.render();
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
    NS.render();
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
    NS.render();
  }

  async function next() {
    if (!canNext()) return;
    if (state.step === 1 && !Object.keys(state.mappings).length) {
      state.mappings = { ...DEFAULT_MAPPINGS };
    }
    // 기본 매핑이 적용된 채로 열 매핑 단계에 진입하면 검증 결과도
    // 즉시 채운다. 사용자가 매핑을 변경한 경우에는 3단계 이동 시
    // 다시 미리보기를 생성한다.
    if (state.step === 1) {
      state.step = 2;
      await _loadPreview();
      await NS.render();
      return;
    }
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
    await NS.render();
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
    if (!state.previewResult) await NS.render();
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

  Object.assign(NS, {
    selectFile,
    toggleSheet,
    setMapping,
    selectMappingSource,
    setSourceMapping,
    toggleConflictDecision,
    handleModalKeydown,
    cancelModal,
    submitModal,
    saveProfile,
    deleteProfile,
    loadProfile,
    selectPolicy,
    setFilter,
    retryInit,
    downloadCsv,
    commit,
    rollback,
    startNewImport,
    goTo,
    next,
    prev,
  });
})(window.__importStudioNS = window.__importStudioNS || {});
