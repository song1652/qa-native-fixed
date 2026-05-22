---
id: tc_236_mybox_select_deselect_x
data_key: valid_user
priority: medium
tags: [positive, mybox, selection, ui]
type: structured
---
# 마이박스 — 파일 선택 후 X 버튼으로 선택 해제 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 체크박스 클릭 (선택)
4. 상단 툴바의 X(닫기) 버튼 클릭
5. 파일 선택 해제 확인

## Expected
- X 버튼 클릭 시 파일 선택이 모두 해제된다
- 툴바가 기본 상태로 돌아간다
