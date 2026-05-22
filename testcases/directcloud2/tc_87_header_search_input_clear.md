---
id: tc_87_header_search_input_clear
data_key: valid_user
priority: low
tags: [positive, search, ui]
type: structured
---
# 검색창 입력 후 내용 지우기 동작 확인

## Precondition
- 로그인 완료 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch)에 test_data[directcloud].search_keyword 입력
3. 검색창 내용을 모두 선택 후 삭제(Ctrl+A → Delete)
4. 검색창 값이 비어있는지 확인

## Expected
- 검색창 내용을 지우면 input 값이 빈 문자열이 된다
