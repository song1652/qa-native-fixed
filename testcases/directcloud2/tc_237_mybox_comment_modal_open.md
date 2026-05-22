---
id: tc_237_mybox_comment_modal_open
data_key: valid_user
priority: medium
tags: [positive, mybox, comment, modal]
type: structured
---
# 마이박스 — 파일 선택 후 코멘트 모달 오픈 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 체크박스 클릭 (선택)
4. 상단 툴바의 코멘트 버튼 클릭
5. 코멘트 모달(#modal-notify-comments) 오픈 확인

## Expected
- 코멘트 모달이 열린다
- 해당 파일의 코멘트 목록이 표시된다
