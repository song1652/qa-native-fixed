---
id: tc_20_search_detail_button
data_key: valid_user
priority: low
tags: [positive, search, ui]
type: structured
---
# 상세 검색 버튼 동작 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 상세 검색 버튼(#search-detail) 가시성 확인
3. 상세 검색 버튼 클릭
4. 검색 실행 버튼(#search-search) 가시성 확인

## Expected
- #search-detail 버튼이 표시된다
- 클릭 후 #search-search 버튼이 표시된다
- 페이지가 정상 반응한다
