---
id: tc_170_ai_home_page_load
data_key: valid_user
priority: medium
tags: [positive, ai, navigation]
type: structured
---
# AI 홈 — 페이지 로드 및 채팅 입력창 확인

## Precondition
- 로그인 완료

## Steps
1. 유효한 자격증명으로 로그인
2. "AI 홈"(li#aihome) 클릭
3. AI 채팅 페이지 로드 확인
4. 질문 입력창(textarea[placeholder*="질문을 입력하세요"]) 존재 확인
5. 전송 버튼 존재 확인

## Expected
- AI 홈 페이지가 로드된다
- 질문 입력창과 전송 버튼이 표시된다
