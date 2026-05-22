---
id: tc_308_ai_chat_message_send
data_key: valid_user
priority: medium
tags: [positive, ai, chat, write, send]
type: structured
---
# AI — 채팅창에 메시지 입력 및 전송

## Precondition
- 로그인 완료, AI 기능 활성화 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 AI 메뉴(li#ai 또는 AI 아이콘) 클릭
3. AI 채팅 입력창 클릭
4. 질문 텍스트 입력 (test_data: ai_chat_message)
5. 전송 버튼 클릭 또는 Enter 키 입력
6. 메시지가 채팅 창에 표시되는지 확인

## Expected
- 입력한 메시지가 채팅 창에 전송되어 표시된다
- AI 응답이 로딩 중 또는 응답 표시 상태가 된다
