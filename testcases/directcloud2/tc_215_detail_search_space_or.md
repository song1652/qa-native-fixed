---
id: tc_215_detail_search_space_or
data_key: valid_user
priority: low
tags: [positive, search, detail-search]
type: structured
---
# 상세 검색 — 검색어 공백 구분: OR 조건 선택 확인

## Precondition
- 로그인 완료, 상세 검색 패널 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch) 클릭
3. 상세 검색 버튼(#search-detail) 클릭
4. 공백 구분 OR 라디오(#detail-space-or) 클릭
5. 선택 상태 확인

## Expected
- OR 조건 라디오 버튼이 선택된다
- 공백으로 구분된 검색어를 OR 조건으로 검색한다
