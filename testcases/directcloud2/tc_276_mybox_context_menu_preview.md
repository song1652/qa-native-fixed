---
id: tc_276_mybox_context_menu_preview
data_key: valid_user
priority: medium
tags: [positive, mybox, context-menu, preview]
type: structured
---
# 마이박스 — 파일 컨텍스트 메뉴 "미리보기" 항목 클릭 확인

## Precondition
- 로그인 완료, 마이박스에 미리보기 가능한 파일 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행 우클릭 → 컨텍스트 메뉴 오픈
4. "미리보기" 항목 클릭
5. 미리보기 모달 오픈 확인

## Expected
- 미리보기 항목 클릭 시 파일 미리보기 모달이 열린다
