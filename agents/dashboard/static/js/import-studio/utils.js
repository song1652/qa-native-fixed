// Import Studio — 순수 유틸 + state 파생 헬퍼
(function (NS) {
  'use strict';

  const { state } = NS;

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

  function getSelectedSheetSources() {
    return state.selectedSources.flatMap((source) => source.sheets.map((sheet) => ({
      fileId: source.fileId,
      sheet,
      key: `${source.fileId}::${sheet}`,
      fileName: state.files.find((file) => file.id === source.fileId)?.name || source.fileId,
    })));
  }

  Object.assign(NS, {
    escHtml,
    getExcelColumns,
    formatSize,
    formatDate,
    errorMessage,
    rowKey,
    unresolvedConflictCount,
    makeIdempotencyKey,
    getSelectedSheetSources,
  });
})(window.__importStudioNS = window.__importStudioNS || {});
