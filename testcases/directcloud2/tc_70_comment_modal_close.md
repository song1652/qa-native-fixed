---
id: tc_70_comment_modal_close
data_key: valid_user
priority: medium
tags: [positive, notification, comment, modal]
type: structured
---
# 코멘트 알림 모달 — 닫기 버튼(X) 동작 확인

## Precondition
- 로그인 완료, 코멘트 알림 모달(#modal-notify-comments) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 헤더 코멘트 알림 버튼(#showNotifyComment) 클릭
3. 모달(#modal-notify-comments) 로드 대기
4. 닫기 버튼(button.close) 클릭

## Expected
- 코멘트 알림 모달이 닫힌다
- 메인 파일 목록(#main)이 다시 표시된다
