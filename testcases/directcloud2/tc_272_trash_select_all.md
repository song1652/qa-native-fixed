---
id: tc_272_trash_select_all
data_key: valid_user
priority: medium
tags: [positive, trash, selection, checkbox]
type: structured
---
# 휴지통 — 전체 선택 체크박스 동작 확인

## Precondition
- 로그인 완료, 휴지통에 파일 최소 2개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "휴지통"(li#trash) 클릭
3. 전체 선택 체크박스 클릭
4. 모든 파일 선택 상태 확인

## Expected
- 전체 선택 체크박스 클릭 시 모든 파일이 선택된다
