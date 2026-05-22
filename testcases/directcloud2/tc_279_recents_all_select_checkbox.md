---
id: tc_279_recents_all_select_checkbox
data_key: valid_user
priority: medium
tags: [positive, recent, files, selection, checkbox]
type: structured
---
# 최근파일 — 전체 선택 체크박스 동작 확인

## Precondition
- 로그인 완료, 최근파일 페이지, 파일 최소 2개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 헤더 전체 선택 체크박스 클릭
4. 모든 파일 선택 상태 확인

## Expected
- 전체 선택 체크박스 클릭 시 모든 최근 파일이 선택된다
