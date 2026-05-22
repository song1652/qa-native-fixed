---
id: tc_27_comment_notification_modal
data_key: valid_user
priority: medium
tags: [positive, notification, modal]
type: structured
---
# 코멘트 알림 모달 열기 및 내용 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 헤더 코멘트 알림 버튼(#showNotifyComment) 클릭
3. 코멘트 알림 모달(#modal-notify-comments) 표시 대기

## Expected
- 코멘트 알림 모달(#modal-notify-comments)이 표시된다
- 모달 내 코멘트 항목이 1개 이상 존재한다
- 닫기 버튼(button.close) 또는 모달 내용이 표시된다
