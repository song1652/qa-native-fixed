// ── App Initialization & Global Actions ──
async function resetTeamDiscussion() {
  if (!(await safeConfirm('팀 토론 기록을 초기화하시겠습니까?'))) return;
  try { await fetch('/api/discuss/reset', { method: 'POST' }); await refreshAll(); showToast('팀 토론 초기화 완료'); }
  catch (e) { showToast('초기화 실패'); }
}

async function submitTopic() {
  if (_uiState.teamTopicSubmitting) return;
  const input = document.getElementById('new-topic-input');
  const btn = document.getElementById('new-topic-btn');
  const setStatus = (message, kind = '') => {
    _uiState.teamTopicStatus = message;
    _uiState.teamTopicStatusClass = 'topic-status' + (kind ? ' ' + kind : '');
    const status = document.getElementById('topic-status');
    if (status) { status.textContent = message; status.className = _uiState.teamTopicStatusClass; }
  };
  const topic = input.value.trim();
  if (!topic) { setStatus('주제를 입력해주세요.', 'err'); return; }
  _uiState.teamTopicSubmitting = true;
  btn.disabled = true;
  setStatus('전송 중…');
  try {
    const res = await fetch('/api/discuss/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ topic }) });
    const data = await res.json();
    if (data.ok) {
      setStatus('주제 등록됨', 'ok');
      if (_uiState.teamTopic.trim() === topic) {
        _uiState.teamTopic = '';
        const currentInput = document.getElementById('new-topic-input');
        if (currentInput) currentInput.value = '';
      }
      showHookAlert('discuss', topic);
    }
    else { setStatus(data.error || '전송 실패', 'err'); }
  } catch (e) { setStatus('서버 연결 오류', 'err'); }
  _uiState.teamTopicSubmitting = false;
  btn.disabled = false;
  const currentButton = document.getElementById('new-topic-btn');
  if (currentButton) currentButton.disabled = false;
}


// ── Bootstrap ──
connectSSE();
refreshAll();
setInterval(refreshAll, 5000);
