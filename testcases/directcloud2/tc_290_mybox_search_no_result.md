---
id: tc_290_mybox_search_no_result
data_key: valid_user
priority: medium
tags: [negative, search, empty-state]
type: structured
---
# 검색 — 결과 없는 검색어 입력 시 빈 상태 메시지 확인

## Precondition
- 로그인 완료

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch)에 존재하지 않는 파일명 입력 (예: "zzz_nonexistent_file_xyz")
3. 검색 실행
4. 빈 상태 메시지 확인

## Expected
- 검색 결과가 없을 때 "검색 결과가 없습니다" 또는 유사한 빈 상태 메시지가 표시된다
