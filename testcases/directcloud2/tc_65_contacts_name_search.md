---
id: tc_65_contacts_name_search
data_key: valid_user
priority: medium
tags: [positive, contacts, search]
type: structured
---
# 주소록 — 이름/이메일 검색 입력 및 검색 버튼 동작 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/contacts 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "주소록"(li#contacts) 클릭
3. 이름/이메일 검색 필드(input[placeholder*="이름 또는 이메일"]) 클릭
4. test_data[directcloud].search_keyword 입력
5. 검색 버튼(button:has-text("검색")) 클릭

## Expected
- 검색 필드에 키워드가 입력된다
- 검색 버튼 클릭 후 결과 또는 빈 목록이 표시된다 (오류 없음)
