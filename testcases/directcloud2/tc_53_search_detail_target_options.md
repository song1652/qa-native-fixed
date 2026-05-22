---
id: tc_53_search_detail_target_options
data_key: valid_user
priority: medium
tags: [positive, search, detail-search, target]
type: structured
---
# 상세 검색 — 검색 대상 체크박스 이름/코멘트/태그/문서 옵션 확인

## Precondition
- 로그인 완료, 상세 검색 패널 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 상세 검색 버튼(#search-detail) 클릭
3. 검색 대상 체크박스 옵션 확인 — 이름(#search-detail-name), 코멘트(#search-detail-comment), 태그(#search-detail-tag), 문서(#search-detail-document)

## Expected
- 4개의 검색 대상 체크박스(이름, 코멘트, 태그, 문서)가 표시된다
- 각 체크박스가 독립적으로 클릭 가능하다
