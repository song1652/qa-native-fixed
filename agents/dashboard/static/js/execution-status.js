// 실행을 재개하지 않고 서버가 추적하는 작업만 표시한다.
var _trackedExecution = null;
var _executionStatusBusy = false;
var _executionCancelBusy = false;

function executionStatusRender() {
  const controls = document.getElementById('execution-controls');
  const status = document.getElementById('execution-status');
  const cancel = document.getElementById('execution-cancel');
  controls.hidden = !_trackedExecution;
  if (!_trackedExecution) return;
  const names = {run_qa: '단일 파이프라인', run_qa_parallel: '병렬 파이프라인', run_merge: '병렬 실행', run_quick: '빠른 실행'};
  const states = {running: '실행 중', cancelling: '중단 중', passed: '완료', failed: '실패', cancelled: '중단', interrupted: '중단', timed_out: '시간 초과'};
  status.textContent = (names[_trackedExecution.tag] || '실행') + ' · ' + (states[_trackedExecution.status] || '상태 확인 필요');
  cancel.hidden = !['running', 'cancelling'].includes(_trackedExecution.status);
  cancel.disabled = _executionCancelBusy || _trackedExecution.status === 'cancelling';
}

async function executionStatusRefresh() {
  if (_executionStatusBusy) return;
  _executionStatusBusy = true;
  try {
    const data = await safeNoticeGet('/api/execution_status');
    if (!data || data.ok !== true) throw new Error('실행 상태 응답 오류');
    _trackedExecution = data.execution || null;
    executionStatusRender();
  } catch (error) {
    if (_trackedExecution) document.getElementById('execution-status').textContent = '연결 확인 필요 · 마지막 실행 상태 유지';
  } finally { _executionStatusBusy = false; }
}

async function cancelTrackedExecution() {
  if (!_trackedExecution || _executionCancelBusy || _trackedExecution.status !== 'running') return;
  const runId = _trackedExecution.run_id;
  _executionCancelBusy = true;
  executionStatusRender();
  try {
    const response = await fetch('/api/cancel', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({run_id: runId})});
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || '실행 중단 요청을 확인하세요.');
    await executionStatusRefresh();
    await recoveryNoticesRefresh();
    await refreshAll();
  } catch (error) {
    showToast(error.message || '서버 연결을 확인하고 실행 상태를 다시 확인하세요.', 'error');
  } finally { _executionCancelBusy = false; executionStatusRender(); }
}

document.getElementById('execution-cancel').addEventListener('click', cancelTrackedExecution);
executionStatusRefresh();
setInterval(executionStatusRefresh, 6000);
