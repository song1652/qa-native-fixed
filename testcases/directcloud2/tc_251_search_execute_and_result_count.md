---
id: tc_251_search_execute_and_result_count
data_key: valid_user
priority: medium
tags: [positive, search, result]
type: structured
---
# 검색 — 검색어 입력 후 결과 건수 표시 확인

## Precondition
- 로그인 완료

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch)에 test_data[directcloud][valid_user].search_keyword 입력
3. 검색 실행 버튼(#search-search) 클릭 또는 Enter
4. 검색 결과 건수 표시 확인

## Expected
- 검색 결과가 표시된다
- 검색 결과 건수 또는 결과 목록이 표시된다
