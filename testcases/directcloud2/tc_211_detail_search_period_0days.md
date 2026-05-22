---
id: tc_211_detail_search_period_0days
data_key: valid_user
priority: low
tags: [positive, search, detail-search, period]
type: structured
---
# 상세 검색 — 기간 오늘(0일) 옵션 선택 확인

## Precondition
- 로그인 완료, 상세 검색 패널 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch) 클릭
3. 상세 검색 버튼(#search-detail) 클릭
4. 기간 0일(오늘) 라디오(#detail-period-0) 클릭
5. 선택 상태 확인

## Expected
- 기간 오늘(0일) 라디오 버튼이 선택된다
