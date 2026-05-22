---
id: tc_196_mybox_select_all_deselect
data_key: valid_user
priority: medium
tags: [positive, mybox, selection, checkbox]
type: structured
---
# 마이박스 — 전체 선택 후 전체 해제 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 2개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 전체 선택 체크박스 클릭 (모든 파일 선택)
4. 전체 파일 선택 상태 확인
5. 전체 선택 체크박스 다시 클릭 (전체 해제)
6. 모든 파일 해제 상태 확인

## Expected
- 전체 선택 체크박스 클릭 시 모든 파일이 선택된다
- 다시 클릭 시 모든 파일 선택이 해제된다
