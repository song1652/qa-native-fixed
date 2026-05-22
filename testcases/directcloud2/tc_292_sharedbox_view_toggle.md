---
id: tc_292_sharedbox_view_toggle
data_key: valid_user
priority: low
tags: [positive, sharedbox, ui, view]
type: structured
---
# 공유박스 — 뷰 전환 버튼 존재 및 동작 확인

## Precondition
- 로그인 완료, 공유박스 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "공유박스"(li#sharedbox) 클릭
3. 뷰 전환 버튼(.btn.btn-files.btn-view) 존재 확인
4. 뷰 전환 버튼 클릭
5. 그리드/목록 뷰 전환 확인

## Expected
- 공유박스 페이지에도 뷰 전환 버튼이 표시된다
- 클릭 시 그리드/목록 뷰가 전환된다
