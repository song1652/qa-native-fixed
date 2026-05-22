---
id: tc_252_search_clear_button
data_key: valid_user
priority: low
tags: [positive, search, ui]
type: structured
---
# 검색 — 검색어 입력 후 초기화(X) 버튼으로 검색어 삭제 확인

## Precondition
- 로그인 완료, 검색창에 검색어 입력된 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch)에 텍스트 입력
3. 검색창 내 X(초기화) 버튼 클릭
4. 검색어 삭제 확인

## Expected
- X 버튼 클릭 시 검색창이 비워진다
