---
id: tc_218_mybox_grid_view_display
data_key: valid_user
priority: low
tags: [positive, mybox, ui, view, grid]
type: structured
---
# 마이박스 — 그리드 뷰 전환 후 파일 카드 형식 표시 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 뷰 전환 버튼 클릭하여 그리드 뷰 전환
4. 파일이 카드(그리드) 형식으로 표시되는지 확인

## Expected
- 그리드 뷰에서 파일이 카드 형식으로 표시된다
- 파일 썸네일이 격자 형태로 배치된다
