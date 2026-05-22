---
id: tc_306_search_keyword_input
data_key: valid_user
priority: high
tags: [positive, search, write, keyword]
type: structured
---
# 검색 — 키워드 직접 입력 후 결과 확인

## Precondition
- 로그인 완료, 검색 가능한 파일 존재

## Steps
1. 유효한 자격증명으로 로그인
2. 상단 검색창(#inputSearch) 클릭
3. 검색어 입력 (test_data: search_keyword)
4. Enter 키 입력 또는 검색 버튼 클릭
5. 검색 결과 목록 표시 확인
6. 검색어를 지우고 다시 다른 키워드 입력 후 검색 결과 변경 확인

## Expected
- 입력한 키워드에 맞는 파일/폴더가 검색 결과에 표시된다
- 검색어 변경 시 결과도 갱신된다
