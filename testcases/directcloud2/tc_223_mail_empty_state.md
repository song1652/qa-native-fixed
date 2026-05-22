---
id: tc_223_mail_empty_state
data_key: valid_user
priority: low
tags: [positive, mail, empty-state]
type: structured
---
# 메일 — 수신 메일 없을 때 빈 상태 메시지 확인

## Precondition
- 로그인 완료, 메일 수신함 0건

## Steps
1. 유효한 자격증명으로 로그인
2. "메일"(li#mail) 클릭
3. 빈 상태 메시지 확인

## Expected
- 수신 메일이 없을 때 빈 상태 메시지가 표시된다
