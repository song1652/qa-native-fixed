---
id: tc_54_search_detail_period_options
data_key: valid_user
priority: low
tags: [positive, search, detail-search, period]
type: structured
---
# 상세 검색 — 기간 옵션 라디오 버튼 확인 (최대/360일/30일/7일/1일)

## Precondition
- 로그인 완료, 상세 검색 패널 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 상세 검색 버튼(#search-detail) 클릭
3. 기간 라디오 옵션 확인 — 최대(#detail-period-max), 360일(#detail-period-360), 30일(#detail-period-30), 7일(#detail-period-7), 1일(#detail-period-1)
4. "30일"(#detail-period-30) 라디오 선택

## Expected
- 기간 라디오 버튼 목록이 표시된다
- #detail-period-30 선택 후 해당 라디오가 checked 상태가 된다
