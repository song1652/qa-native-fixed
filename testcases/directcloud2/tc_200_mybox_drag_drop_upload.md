---
id: tc_200_mybox_drag_drop_upload
data_key: valid_user
priority: medium
tags: [positive, mybox, upload, drag-drop]
type: structured
---
# 마이박스 — 드래그 앤 드롭 업로드 영역 존재 확인

## Precondition
- 로그인 완료, 마이박스 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 목록 영역에 dragover 이벤트 발생
4. 드롭존 표시 확인

## Expected
- 드래그 시 드롭 가능한 영역이 표시된다
- 파일을 드롭할 수 있는 UI 힌트가 제공된다
