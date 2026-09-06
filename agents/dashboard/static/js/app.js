// ── App Initialization & Global Actions ──
async function resetTeamDiscussion() {
  if (!(await safeConfirm('팀 토론 기록을 초기화하시겠습니까?'))) return;
  try { await fetch('/api/discuss/reset', { method: 'POST' }); await refreshAll(); showToast('팀 토론 초기화 완료'); }
  catch (e) { showToast('초기화 실패'); }
}

async function submitTopic() {
  const input = document.getElementById('new-topic-input');
  const btn = document.getElementById('new-topic-btn');
  const status = document.getElementById('topic-status');
  const topic = input.value.trim();
  if (!topic) { status.textContent = '주제를 입력해주세요.'; status.className = 'topic-status err'; return; }
  btn.disabled = true;
  status.textContent = '전송 중...'; status.className = 'topic-status';
  try {
    const res = await fetch('/api/discuss/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ topic }) });
    const data = await res.json();
    if (data.ok) { status.textContent = '주제 등록됨'; status.className = 'topic-status ok'; input.value = ''; showHookAlert('discuss', topic); }
    else { status.textContent = data.error || '전송 실패'; status.className = 'topic-status err'; }
  } catch (e) { status.textContent = '서버 연결 오류'; status.className = 'topic-status err'; }
  btn.disabled = false;
}


// ── Bootstrap ──
connectSSE();
refreshAll();
setInterval(refreshAll, 5000);
