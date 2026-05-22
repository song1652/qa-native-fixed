---
id: tc_133_mybox_view_toggle_grid
data_key: valid_user
priority: low
tags: [positive, mybox, ui, view]
type: structured
---
# 마이박스 — 뷰 전환 버튼(그리드/목록) 존재 확인

## Precondition
- 로그인 완료
- 마이박스(/mybox) 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 뷰 전환 버튼(.btn.btn-files.btn-view.clearfix) 존재 확인

## Expected
- 뷰 전환 버튼이 표시된다
