---
id: tc_259_ai_chat_empty_state
data_key: valid_user
priority: low
tags: [positive, ai, chat, empty-state]
type: structured
---
# AI 홈 — 대화 이력 없을 때 초기 안내 메시지 확인

## Precondition
- 로그인 완료, AI 홈 페이지, 대화 이력 없음

## Steps
1. 유효한 자격증명으로 로그인
2. "AI 홈"(li#aihome) 클릭
3. 초기 안내 메시지 또는 예시 질문 표시 확인

## Expected
- 대화 이력이 없을 때 초기 안내 메시지 또는 사용법이 표시된다
