---
id: tc_120_search_ocr_document_filter
data_key: valid_user
priority: low
tags: [positive, search, detail-search, document]
type: structured
---
# 상세 검색 — 문서(document) 대상 체크박스 선택 후 검색 실행

## Precondition
- 로그인 완료, 상세 검색 패널 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 상세 검색 버튼(#search-detail) 클릭
3. 문서 대상 체크박스(#search-detail-document) 클릭
4. 검색창(#inputSearch)에 test_data[directcloud].search_keyword 입력
5. 검색 실행(#search-search) 클릭

## Expected
- #search-detail-document 체크박스가 선택된다
- 검색 실행 후 오류 없이 결과가 표시된다
