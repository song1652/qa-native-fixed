---
id: tc_227_mybox_search_within
data_key: valid_user
priority: medium
tags: [positive, mybox, search, filter]
type: structured
---
# 마이박스 — 현재 위치 내 검색 결과 확인

## Precondition
- 로그인 완료, 마이박스 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 검색창(#inputSearch)에 검색어 입력
4. 상세 검색에서 범위를 "현재 위치"(#detail-search-current)로 선택
5. 검색 실행

## Expected
- 마이박스 내 파일만 검색 결과에 표시된다
