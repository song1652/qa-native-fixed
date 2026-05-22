---
id: tc_68_comment_modal_total_count
data_key: valid_user
priority: medium
tags: [positive, notification, comment, modal]
type: structured
---
# 코멘트 알림 모달 — 총 코멘트 건수 텍스트 표시 확인

## Precondition
- 로그인 완료, 코멘트 알림 모달(#modal-notify-comments) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 헤더 코멘트 알림 버튼(#showNotifyComment) 클릭
3. 모달(#modal-notify-comments) 로드 대기
4. "총 N건의 코멘트" 텍스트 포함 여부 확인

## Expected
- #modal-notify-comments 모달이 표시된다
- "총" + "코멘트" 텍스트가 모달 내에 포함된다
