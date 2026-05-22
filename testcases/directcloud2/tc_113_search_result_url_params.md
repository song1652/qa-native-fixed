---
id: tc_113_search_result_url_params
data_key: valid_user
priority: medium
tags: [positive, search, url]
type: structured
---
# 검색 실행 후 URL 파라미터 구조 확인 (keyword, category, period 등)

## Precondition
- 로그인 완료 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch)에 test_data[directcloud].search_keyword 입력
3. Enter 키로 검색 실행
4. 검색 결과 URL 파라미터 확인

## Expected
- URL에 "keyword=" 파라미터가 포함된다
- URL에 "/search" 경로가 포함된다
- URL에 "period=" 또는 "category=" 파라미터가 포함된다
