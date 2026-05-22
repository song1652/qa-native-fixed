---
id: tc_51_search_detail_panel_open
data_key: valid_user
priority: medium
tags: [positive, search, detail-search]
type: structured
---
# 상세 검색 패널 열기 — 검색 범위/대상/기간 옵션 표시 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 상세 검색 버튼(#search-detail) 클릭
3. 상세 검색 패널 옵션 확인

## Expected
- 검색 범위 라디오 버튼(#detail-search-all, #detail-search-my 등)이 표시된다
- 검색 대상 체크박스(#search-detail-name, #search-detail-comment 등)가 표시된다
- 기간 옵션 라디오 버튼(#detail-period-max 등)이 표시된다
