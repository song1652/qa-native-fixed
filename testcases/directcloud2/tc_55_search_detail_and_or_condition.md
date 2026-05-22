---
id: tc_55_search_detail_and_or_condition
data_key: valid_user
priority: low
tags: [positive, search, detail-search, condition]
type: structured
---
# 상세 검색 — AND/OR 조건 라디오 버튼 선택 확인

## Precondition
- 로그인 완료, 상세 검색 패널 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 상세 검색 버튼(#search-detail) 클릭
3. AND 조건(#detail-space-and) 라디오 표시 확인
4. OR 조건(#detail-space-or) 라디오 클릭
5. #detail-space-or 선택 상태 확인

## Expected
- AND/OR 조건 라디오 버튼 2개가 표시된다
- #detail-space-or 클릭 시 해당 라디오가 선택된다
