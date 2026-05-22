---
id: tc_143_contacts_empty_state
data_key: valid_user
priority: low
tags: [positive, contacts, empty-state]
type: structured
---
# 연락처 — 등록된 연락처 없을 때 빈 상태 메시지 확인

## Precondition
- 로그인 완료, 연락처 페이지, 연락처 0건

## Steps
1. 유효한 자격증명으로 로그인
2. "연락처"(li#contacts) 클릭
3. 빈 상태 메시지 확인

## Expected
- "등록된 연락처가 없습니다." 메시지가 표시된다
