---
id: tc_110_mail_page_empty_state
data_key: valid_user
priority: low
tags: [positive, mail, empty-state]
type: structured
---
# Mail 페이지 — 발송 이력 없는 빈 상태 메시지 표시 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/mail 페이지, 발송 이력 없음

## Steps
1. 유효한 자격증명으로 로그인
2. "Mail"(li#mail) 클릭
3. 빈 상태 메시지("이메일 발송 내역이 없습니다.") 텍스트 확인

## Expected
- "이메일 발송 내역이 없습니다." 텍스트가 표시된다
