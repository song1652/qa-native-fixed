---
id: tc_225_mybox_upload_button
data_key: valid_user
priority: high
tags: [positive, mybox, upload, ui]
type: structured
---
# 마이박스 — 파일 업로드 버튼 존재 확인

## Precondition
- 로그인 완료, 마이박스 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 업로드 버튼 존재 확인

## Expected
- 파일 업로드 버튼이 표시된다
- 클릭 시 파일 선택 다이얼로그가 열린다
