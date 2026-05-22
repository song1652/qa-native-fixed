---
id: tc_84_search_period_7days
data_key: valid_user
priority: low
tags: [positive, search, detail-search, period]
type: structured
---
# 상세 검색 — 기간 7일 선택 후 검색 실행

## Precondition
- 로그인 완료, 상세 검색 패널 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 상세 검색 버튼(#search-detail) 클릭
3. 기간 "7일"(#detail-period-7) 라디오 클릭
4. 검색창(#inputSearch)에 test_data[directcloud].search_keyword 입력
5. 검색 실행(#search-search) 클릭

## Expected
- #detail-period-7 라디오가 선택된다
- 검색 실행 후 오류 없이 결과가 표시된다
