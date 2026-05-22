---
id: tc_157_detail_search_save_settings
data_key: valid_user
priority: low
tags: [positive, search, detail-search, settings]
type: structured
---
# 상세 검색 — 검색설정 저장 체크박스 확인

## Precondition
- 로그인 완료, 상세 검색 패널 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch) 클릭
3. 상세 검색 버튼(#search-detail) 클릭
4. 검색설정 저장 체크박스(#input-search-settings-save) 존재 확인
5. 체크박스 클릭하여 선택/해제 상태 확인

## Expected
- 검색설정 저장 체크박스가 표시된다
- 클릭 시 체크/해제된다
