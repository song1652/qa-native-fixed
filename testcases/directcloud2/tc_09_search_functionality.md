---
id: tc_09_search_functionality
data_key: valid_user
priority: high
tags: [positive, files, search]
type: structured
---
# 검색 기능 동작 확인

## Precondition
- https://web.directcloud.jp/login 접속 후 정상 로그인 상태

## Steps
1. 유효한 자격증명으로 로그인 (tc_01 동일 절차)
2. 검색창(#inputSearch) 클릭
3. test_data[directcloud].search_keyword 입력
4. Enter 키 입력

## Expected
- 검색창(#inputSearch)이 표시된다
- 입력한 키워드가 검색창에 반영된다
- Enter 입력 후 검색 결과 또는 화면 변화가 발생한다
