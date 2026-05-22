---
id: tc_158_mybox_copy_context_menu
data_key: valid_user
priority: medium
tags: [positive, mybox, context-menu, copy]
type: structured
---
# 마이박스 — 파일 복사 컨텍스트 메뉴 → 폴더 선택 모달 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴에서 "복사" 항목 클릭
5. 폴더 선택 모달 오픈 확인

## Expected
- 복사 컨텍스트 메뉴 클릭 시 복사 대상 폴더 선택 모달이 열린다
