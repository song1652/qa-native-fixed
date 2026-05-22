---
id: tc_249_mybox_context_menu_close_on_outside
data_key: valid_user
priority: low
tags: [positive, mybox, context-menu, ui]
type: structured
---
# 마이박스 — 컨텍스트 메뉴 외부 클릭 시 닫힘 확인

## Precondition
- 로그인 완료, 마이박스 파일 우클릭으로 컨텍스트 메뉴 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행 우클릭으로 컨텍스트 메뉴 오픈
4. 컨텍스트 메뉴 외부 영역 클릭

## Expected
- 외부 클릭 시 컨텍스트 메뉴가 닫힌다
