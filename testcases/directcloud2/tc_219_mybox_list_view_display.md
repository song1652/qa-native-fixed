---
id: tc_219_mybox_list_view_display
data_key: valid_user
priority: low
tags: [positive, mybox, ui, view, list]
type: structured
---
# 마이박스 — 목록 뷰에서 파일 행 형식 표시 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 목록 뷰 상태 확인 (기본값)
4. 파일이 행(row) 형식으로 표시되는지 확인

## Expected
- 목록 뷰에서 파일이 행 형식으로 표시된다
- 이름, 크기, 날짜 등 컬럼이 나란히 표시된다
