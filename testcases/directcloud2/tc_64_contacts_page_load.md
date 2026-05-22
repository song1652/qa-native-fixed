---
id: tc_64_contacts_page_load
data_key: valid_user
priority: medium
tags: [positive, contacts, navigation]
type: structured
---
# 주소록(contacts) 페이지 이동 및 기본 UI 확인

## Precondition
- 로그인 완료 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 "주소록"(li#contacts) 클릭

## Expected
- URL이 https://web.directcloud.jp/contacts 로 변경된다
- "개인 주소록" 버튼(button:has-text("개인 주소록"))이 표시된다
- 이름/이메일 검색 입력 필드(input[placeholder*="이름 또는 이메일"])가 표시된다
