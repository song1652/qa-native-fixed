// ── Team Discussion View ──
function renderMessage(msg, tabId, sessIdx, msgIdx) {
  const roleLabel = ROLE_LABEL[msg.from] || msg.from;
  const roleClass = ROLE_CLASS[msg.from] || '';
  const bubbleClass = BUBBLE_CLASS[msg.from] || '';
  const uid = `${tabId}_${sessIdx}_${msgIdx}`;

  let planToggle = '';
  const plan = msg.metadata && msg.metadata.proposed_plan;
  if (plan) {
    const planJson = esc(JSON.stringify(plan, null, 2));
    planToggle = `<button class="plan-toggle" onclick="togglePlan('${uid}')">&#9654; proposed_plan 보기</button><div class="plan-body" id="plan-${uid}">${planJson}</div>`;
  }

  let statusTag = '';
  if (msg.status && MSG_STATUS_STYLE[msg.status]) {
    const label = msg.status === 'approved' ? '&#10003; 승인' : '&#8617; 수정 요청';
    statusTag = `<span class="msg-status-tag" style="${MSG_STATUS_STYLE[msg.status]}">${label}</span>`;
  }

  return `<div class="msg"><div class="msg-meta"><span class="role-badge ${roleClass}">${roleLabel}</span><span>${fmtTime(msg.timestamp)}</span></div><div class="msg-bubble ${bubbleClass}">${esc(msg.content)}</div>${planToggle}${statusTag}</div>`;
}

function renderSession(session, tabId, idx) {
  const stageLabel = session.stage_label || session.stage;
  const statusLabel = STATUS_LABEL[session.status] || session.status;
  const statusClass = STATUS_CLASS[session.status] || '';
  const key = `${tabId}_${idx}`;
  const collapsed = (collapsedSessions[tabId] || new Set()).has(idx);

  const msgsHtml = session.messages && session.messages.length
    ? session.messages.map((m, mi) => renderMessage(m, tabId, idx, mi)).join('')
    : '<div class="waiting-msg">대화 대기 중...</div>';

  const isDiscussed = session.stage === 'team_discussion' && session.status === 'discussed';
  let approveBar = '';
  if (isDiscussed) {
    const items = session.conclusion_items;
    approveBar = items ? renderVoteSection(key, items) : '';
  }

  return `<div class="session" id="sess-${key}"><button type="button" class="session-header" onclick="toggleSession('${tabId}',${idx})" aria-expanded="${!collapsed}"><span class="session-stage">${stageLabel}</span><span class="status-badge ${statusClass}">${statusLabel}</span><span class="session-toggle" id="stgl-${key}" aria-hidden="true">${collapsed ? '&#9654;' : '&#9660;'}</span></button><div class="messages${collapsed ? ' collapsed' : ''}" id="msgs-${key}">${msgsHtml}</div>${approveBar}</div>`;
}

function renderTeamView(main) {
  if (!lastData) return;
  let sessions = [];
  if (currentView.startsWith('team_')) {
    const idx = parseInt(currentView.replace('team_', ''));
    const ts = lastData.team_sessions || [];
    sessions = ts[idx] ? [ts[idx]] : [];
  }
  if (!sessions.length) {
    main.innerHTML = '<div class="empty"><div class="empty-icon">&#x1F4AC;</div><h2>토론 대기 중</h2><p>왼쪽 패널에서 주제를 입력하고 토론을 시작하세요</p></div>';
    return;
  }
  main.innerHTML = sessions.map((s, i) => renderSession(s, currentView, i)).join('');
}

function renderVoteSection(key, items) {
  const total = items.length;
  const done = items.filter(i => i.status !== 'pending').length;
  const itemsHtml = items.map(item => {
    let actionHtml;
    if (item.status === 'approved') actionHtml = '<span class="vote-tag vote-tag-approve">&#10003; 승인</span>';
    else if (item.status === 'rejected') actionHtml = '<span class="vote-tag vote-tag-reject">&#10007; 반려</span>';
    else actionHtml = `<button type="button" class="vote-btn-n" aria-label="반려" onclick="event.stopPropagation();voteItem('${key}',${item.id},'reject')">&#10007;</button><button type="button" class="vote-btn-y" onclick="event.stopPropagation();voteItem('${key}',${item.id},'approve')">&#10003; 승인</button>`;
    return `<div class="vote-item" id="vi-${key}-${item.id}" data-status="${esc(item.status)}" tabindex="0" role="button" aria-label="${esc(item.title)} 항목 펼치기" onclick="toggleVoteItem('${key}',${item.id})" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();toggleVoteItem('${key}',${item.id})}"><div class="vote-item-top"><span class="vote-item-title">${esc(item.title)}</span><div id="va-${key}-${item.id}">${actionHtml}</div></div><div class="vote-item-body">${esc(item.text)}</div></div>`;
  }).join('');
  return `<div class="vote-section"><div class="vote-section-header"><span class="vote-section-label">항목별 검토</span><span class="vote-progress" id="vp-${key}">${done} / ${total} 완료</span></div><div id="vitems-${key}">${itemsHtml}</div></div>`;
}

function togglePlan(uid) {
  const body = document.getElementById('plan-' + uid);
  if (!body) return;
  body.classList.toggle('open');
}

function toggleSession(tabId, idx) {
  const key = `${tabId}_${idx}`;
  const msgs = document.getElementById('msgs-' + key);
  if (!msgs) return;
  const collapsed = msgs.classList.toggle('collapsed');
  const tgl = document.getElementById('stgl-' + key);
  if (tgl) tgl.textContent = collapsed ? '\u25B6' : '\u25BC';
  if (!collapsedSessions[tabId]) collapsedSessions[tabId] = new Set();
  if (collapsed) collapsedSessions[tabId].add(idx);
  else collapsedSessions[tabId].delete(idx);
}

function toggleVoteItem(key, id) {
  const el = document.getElementById(`vi-${key}-${id}`);
  if (el) el.classList.toggle('collapsed');
}

async function voteItem(key, itemId, vote) {
  const actEl = document.getElementById(`va-${key}-${itemId}`);
  const itemEl = document.getElementById(`vi-${key}-${itemId}`);
  if (actEl) actEl.innerHTML = '<span style="font-size:11px;color:var(--text-dim)">&#9203;</span>';
  try {
    const res = await fetch('/api/discuss/vote_item', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: itemId, vote }),
    });
    const data = await res.json();
    if (!data.ok) { if (actEl) actEl.innerHTML = '<span style="color:var(--revision-color);font-size:11px">오류</span>'; return; }
    const status = vote === 'approve' ? 'approved' : 'rejected';
    if (itemEl) itemEl.dataset.status = status;
    if (actEl) actEl.innerHTML = status === 'approved' ? '<span class="vote-tag vote-tag-approve">&#10003; 승인</span>' : '<span class="vote-tag vote-tag-reject">&#10007; 반려</span>';
    const progEl = document.getElementById(`vp-${key}`);
    if (progEl) {
      const all = document.querySelectorAll(`#vitems-${key} .vote-item`);
      const doneCnt = Array.from(all).filter(el => el.dataset.status !== 'pending').length;
      progEl.textContent = `${doneCnt} / ${all.length} 완료`;
    }
    if (data.all_voted) {
      showHookAlert('discuss_approved', '승인된 항목이 team_notes에 저장되었습니다');
      setTimeout(() => { lastJson = ''; refreshAll(); }, 600);
    }
  } catch (e) {
    if (actEl) actEl.innerHTML = `<span style="color:var(--revision-color);font-size:11px">오류</span>`;
  }
}
