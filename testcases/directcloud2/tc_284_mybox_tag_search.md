---
id: tc_284_mybox_tag_search
data_key: valid_user
priority: medium
tags: [positive, search, tag]
type: structured
---
# 검색 — 태그로 파일 검색 결과 확인

## Precondition
- 로그인 완료, 태그가 붙은 파일 존재

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch)에 태그명 입력
3. 상세 검색에서 태그 필터(#search-detail-tag) 선택
4. 검색 실행
5. 해당 태그가 붙은 파일 검색 결과 확인

## Expected
- 태그 검색 결과로 해당 태그가 붙은 파일이 표시된다
