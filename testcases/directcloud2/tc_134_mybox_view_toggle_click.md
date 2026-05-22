---
id: tc_134_mybox_view_toggle_click
data_key: valid_user
priority: low
tags: [positive, mybox, ui, view]
type: structured
---
# 마이박스 — 뷰 전환 버튼 클릭 시 뷰 변경 확인

## Precondition
- 로그인 완료
- 마이박스 페이지
- 파일/폴더 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 뷰 전환 버튼 클릭
4. 뷰 변경 확인
5. 다시 클릭하여 원래 뷰로 복귀 확인

## Expected
- 뷰 전환 버튼 클릭 시 그리드/목록 뷰가 전환된다
