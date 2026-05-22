---
id: tc_250_mybox_search_name_filter
data_key: valid_user
priority: medium
tags: [positive, search, name, filter]
type: structured
---
# 상세 검색 — 파일명 필터 체크박스 선택 확인

## Precondition
- 로그인 완료, 상세 검색 패널 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch) 클릭
3. 상세 검색 버튼(#search-detail) 클릭
4. 파일명 검색 체크박스(#search-detail-name) 클릭
5. 선택 상태 확인

## Expected
- 파일명 필터 체크박스가 선택된다
- 파일명으로 검색 범위가 설정된다
