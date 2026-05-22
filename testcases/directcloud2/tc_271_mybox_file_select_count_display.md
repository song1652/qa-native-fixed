---
id: tc_271_mybox_file_select_count_display
data_key: valid_user
priority: low
tags: [positive, mybox, selection, ui]
type: structured
---
# 마이박스 — 파일 다중 선택 시 선택 건수 표시 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 3개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 체크박스 3개 클릭 (다중 선택)
4. 선택 건수 표시 확인

## Expected
- 선택된 파일 수(예: "3개 선택됨")가 표시된다
