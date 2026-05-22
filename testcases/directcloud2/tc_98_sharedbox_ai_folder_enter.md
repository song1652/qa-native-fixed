---
id: tc_98_sharedbox_ai_folder_enter
data_key: valid_user
priority: high
tags: [positive, shared, ai, navigation]
type: structured
---
# Shared Box — "DirectCloud AI" 폴더 진입 및 AI 채팅 인터페이스 확인

## Precondition
- 로그인 완료, Shared Box 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "Shared Box"(li#sharedbox) 클릭
3. "DirectCloud AI" 폴더명 클릭
4. AI 채팅 인터페이스 로드 대기

## Expected
- URL이 /sharedbox/ 하위 경로로 변경된다
- AI 채팅 입력창(textarea[placeholder*="질문을 입력하세요"]) 가 표시된다
- "전송" 버튼이 표시된다
