---
id: tc_69_comment_modal_detail_buttons
data_key: valid_user
priority: low
tags: [positive, notification, comment, modal]
type: structured
---
# 코멘트 알림 모달 — 각 코멘트별 "상세" 버튼 개수 확인

## Precondition
- 로그인 완료, 코멘트 알림 모달(#modal-notify-comments) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 헤더 코멘트 알림 버튼(#showNotifyComment) 클릭
3. 모달(#modal-notify-comments) 로드 대기
4. "상세" 버튼 개수 확인

## Expected
- "상세" 버튼이 1개 이상 존재한다
- "더 보기" 버튼이 표시된다
