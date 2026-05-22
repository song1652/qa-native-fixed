---
id: tc_75_link_history_search_execute
data_key: valid_user
priority: medium
tags: [positive, link, search]
type: structured
---
# Link History — 필터 조합 후 검색 버튼 실행

## Precondition
- 로그인 완료, https://web.directcloud.jp/linkmanager 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "Link History"(li#linkmanager) 클릭
3. 필터 select에서 "전체"(value=all) 선택
4. 파일명/링크 입력 필드(input[placeholder="파일명 / 링크"])에 test_data[directcloud].search_keyword 입력
5. "검색" 버튼(button:has-text("검색")) 클릭

## Expected
- 검색 버튼 클릭 후 결과 또는 빈 목록이 표시된다
- 오류 없이 페이지가 반응한다
