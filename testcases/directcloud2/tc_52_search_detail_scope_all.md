---
id: tc_52_search_detail_scope_all
data_key: valid_user
priority: medium
tags: [positive, search, detail-search, scope]
type: structured
---
# 상세 검색 — 검색 범위 "전체" 선택 확인

## Precondition
- 로그인 완료, 상세 검색 패널 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 상세 검색 버튼(#search-detail) 클릭
3. 검색 범위 라디오 "전체"(#detail-search-all) 클릭
4. 검색창(#inputSearch)에 test_data[directcloud].search_keyword 입력
5. 검색 실행 버튼(#search-search) 클릭

## Expected
- #detail-search-all 라디오가 선택된다
- 검색 실행 후 오류 없이 결과가 표시된다
