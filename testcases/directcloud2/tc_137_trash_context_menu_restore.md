---
id: tc_137_trash_context_menu_restore
data_key: valid_user
priority: high
tags: [positive, trash, context-menu, restore]
type: structured
---
# 휴지통 — 파일 우클릭 컨텍스트 메뉴 복구 항목 확인

## Precondition
- 로그인 완료, 휴지통에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "휴지통"(li#trash) 클릭
3. 파일 행 우클릭 → 컨텍스트 메뉴 오픈
4. "복구" 항목(.menu-복구-wrap) 존재 확인

## Expected
- 컨텍스트 메뉴에 "복구" 항목이 표시된다
