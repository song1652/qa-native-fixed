---
id: tc_186_search_tag_filter
data_key: valid_user
priority: medium
tags: [positive, search, tag, filter]
type: structured
---
# 상세 검색 — 태그 필터 체크박스 선택 확인

## Precondition
- 로그인 완료, 상세 검색 패널 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch) 클릭
3. 상세 검색 버튼(#search-detail) 클릭
4. 태그 검색 체크박스(#search-detail-tag) 클릭
5. 선택 상태 확인

## Expected
- 태그 필터 체크박스가 선택된다
- 태그로 검색 범위가 설정된다
