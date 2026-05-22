---
id: tc_115_link_history_type_create_filter
data_key: valid_user
priority: low
tags: [positive, link, filter]
type: structured
---
# Link History — 필터 "생성"(create) 선택 후 검색 실행

## Precondition
- 로그인 완료, https://web.directcloud.jp/linkmanager 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "Link History"(li#linkmanager) 클릭
3. 필터 select에서 "생성"(value=create) 선택
4. "검색" 버튼(button:has-text("검색")) 클릭

## Expected
- "생성" 필터가 선택된다
- 검색 버튼 클릭 후 페이지가 오류 없이 반응한다
