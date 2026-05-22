---
id: tc_159_mybox_move_context_menu
data_key: valid_user
priority: medium
tags: [positive, mybox, context-menu, move]
type: structured
---
# 마이박스 — 파일 이동 컨텍스트 메뉴 → 폴더 선택 모달 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴에서 "이동" 항목 클릭
5. 폴더 선택 모달 오픈 확인

## Expected
- 이동 컨텍스트 메뉴 클릭 시 이동 대상 폴더 선택 모달이 열린다
