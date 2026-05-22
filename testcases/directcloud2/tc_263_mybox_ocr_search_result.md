---
id: tc_263_mybox_ocr_search_result
data_key: valid_user
priority: medium
tags: [positive, search, ocr, document]
type: structured
---
# 검색 — OCR 문서 필터 선택 후 검색 결과 확인

## Precondition
- 로그인 완료, OCR 처리된 파일 존재

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch)에 검색어 입력
3. 상세 검색 버튼(#search-detail) 클릭
4. 문서 내용 체크박스(#search-detail-document) 선택
5. 검색 실행
6. OCR 문서 검색 결과 확인

## Expected
- OCR 문서 필터 선택 시 문서 내용 기반 검색 결과가 표시된다
