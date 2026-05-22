---
id: tc_99_ai_chat_input_visible
data_key: valid_user
priority: high
tags: [positive, ai, chat, ui]
type: structured
---
# AI 폴더 내 채팅 입력창 — 텍스트 입력 동작 확인

## Precondition
- 로그인 완료, Shared Box > DirectCloud AI 폴더 진입 상태

## Steps
1. 유효한 자격증명으로 로그인
2. "Shared Box"(li#sharedbox) 클릭
3. "DirectCloud AI" 폴더 클릭
4. AI 채팅 입력창(textarea[placeholder*="질문을 입력하세요"]) 클릭
5. test_data[directcloud].search_keyword 입력

## Expected
- 채팅 입력창이 표시된다
- 텍스트 입력 시 입력값이 반영된다
- "전송" 버튼이 표시된다
