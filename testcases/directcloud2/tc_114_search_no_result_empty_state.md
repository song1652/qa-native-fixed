---
id: tc_114_search_no_result_empty_state
data_key: valid_user
priority: low
tags: [negative, search, empty-state]
type: structured
---
# 검색 결과 없음 — 존재하지 않는 키워드 검색 시 빈 결과 표시

## Precondition
- 로그인 완료 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 검색창(#inputSearch)에 "xyznonexistentkeyword12345" 입력
3. Enter 키로 검색 실행
4. 검색 결과 영역 확인

## Expected
- 검색이 실행된다 (URL에 keyword 파라미터 포함)
- 파일 항목(.checkbox-list-item)이 0개이거나 빈 목록 메시지가 표시된다
- 오류 없이 페이지가 반응한다
