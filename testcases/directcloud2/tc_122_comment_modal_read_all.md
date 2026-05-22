---
id: tc_122_comment_modal_read_all
data_key: valid_user
priority: low
tags: [positive, notification, comment, modal]
type: structured
---
# 코멘트 알림 모달 — "모두 읽음 표시" 버튼 표시 확인

## Precondition
- 로그인 완료, 코멘트 알림 모달(#modal-notify-comments) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 헤더 코멘트 알림 버튼(#showNotifyComment) 클릭
3. 코멘트 알림 모달(#modal-notify-comments) 로드 대기
4. "모두 읽음 표시" 링크 또는 버튼 가시성 확인

## Expected
- "모두 읽음 표시" 텍스트를 포함한 UI 요소가 표시된다
