---
id: tc_123_comment_modal_load_more
data_key: valid_user
priority: low
tags: [positive, notification, comment, modal]
type: structured
---
# 코멘트 알림 모달 — "더 보기" 버튼 표시 및 클릭 동작 확인

## Precondition
- 로그인 완료, 코멘트 알림 모달(#modal-notify-comments) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 헤더 코멘트 알림 버튼(#showNotifyComment) 클릭
3. 코멘트 알림 모달 로드 대기
4. "더 보기" 버튼(button:has-text("더 보기")) 가시성 확인
5. "더 보기" 버튼 클릭

## Expected
- "더 보기" 버튼이 표시된다
- 클릭 후 페이지가 오류 없이 반응한다
