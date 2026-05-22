---
id: tc_239_link_manager_expiry_display
data_key: valid_user
priority: low
tags: [positive, link-manager, expiry, ui]
type: structured
---
# 링크 관리 — 링크 만료일 표시 확인

## Precondition
- 로그인 완료, 링크 관리 페이지, 만료일 설정된 링크 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "링크 관리"(li#linkmanager) 클릭
3. 링크 목록에서 만료일 컬럼 확인

## Expected
- 링크의 만료일이 목록에 표시된다
