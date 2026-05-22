---
id: tc_189_search_share_scope
data_key: valid_user
priority: low
tags: [positive, search, scope, filter]
type: structured
---
# 상세 검색 — 검색 범위: 공유박스 선택 확인

## Precondition
- 로그인 완료, 상세 검색 패널 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch) 클릭
3. 상세 검색 버튼(#search-detail) 클릭
4. 검색 범위 라디오에서 공유박스(#detail-search-share) 클릭
5. 선택 상태 확인

## Expected
- 공유박스 범위 라디오 버튼이 선택된다
