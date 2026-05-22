---
id: tc_295_link_manager_empty_state
data_key: valid_user
priority: low
tags: [positive, link-manager, empty-state]
type: structured
---
# 링크 관리 — 링크 없을 때 빈 상태 메시지 확인

## Precondition
- 로그인 완료, 링크 관리 페이지, 생성된 링크 0건

## Steps
1. 유효한 자격증명으로 로그인
2. "링크 관리"(li#linkmanager) 클릭
3. 빈 상태 메시지 확인

## Expected
- 링크가 없을 때 빈 상태 메시지가 표시된다
