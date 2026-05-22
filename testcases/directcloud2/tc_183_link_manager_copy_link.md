---
id: tc_183_link_manager_copy_link
data_key: valid_user
priority: medium
tags: [positive, link-manager, copy]
type: structured
---
# 링크 관리 — 링크 복사 버튼 확인

## Precondition
- 로그인 완료, 링크 관리 페이지, 링크 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "링크 관리"(li#linkmanager) 클릭
3. 링크 항목의 복사 버튼 존재 확인
4. 복사 버튼 클릭

## Expected
- 링크 복사 버튼이 표시된다
- 클릭 시 링크가 클립보드에 복사된다
