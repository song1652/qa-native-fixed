---
id: tc_100_ai_chat_send_button
data_key: valid_user
priority: medium
tags: [positive, ai, chat]
type: structured
---
# AI 폴더 — 채팅 전송 버튼 클릭 동작 확인

## Precondition
- 로그인 완료, Shared Box > DirectCloud AI 폴더 진입, 채팅 입력창 표시 상태

## Steps
1. 유효한 자격증명으로 로그인
2. "Shared Box"(li#sharedbox) → "DirectCloud AI" 폴더 클릭
3. 채팅 입력창에 test_data[directcloud].search_keyword 입력
4. "전송" 버튼 클릭

## Expected
- "전송" 버튼이 클릭 가능한 상태다
- 클릭 후 페이지가 오류 없이 반응한다
