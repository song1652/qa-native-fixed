---
id: tc_210_comment_modal_add_comment
data_key: valid_user
priority: medium
tags: [positive, comment, modal]
type: structured
---
# 코멘트 모달 — 새 코멘트 입력 및 등록 확인

## Precondition
- 로그인 완료, 코멘트 모달(#modal-notify-comments) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 파일 선택 후 코멘트 모달 오픈
3. 코멘트 입력 필드에 텍스트 입력
4. 등록 버튼 클릭
5. 코멘트 목록에 새 코멘트 표시 확인

## Expected
- 새 코멘트가 등록된다
- 코멘트 목록에 방금 입력한 내용이 표시된다
