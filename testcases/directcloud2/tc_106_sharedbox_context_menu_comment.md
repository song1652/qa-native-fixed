---
id: tc_106_sharedbox_context_menu_comment
data_key: valid_user
priority: medium
tags: [positive, files, context-menu, comment]
type: structured
---
# Shared Box 파일 우클릭 → 코멘트 설정 메뉴 항목 확인

## Precondition
- 로그인 완료, Shared Box > DirectCloud AI 폴더 내 파일 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "Shared Box"(li#sharedbox) → "DirectCloud AI" 폴더 클릭
3. 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴에서 "코멘트 설정" 항목 가시성 확인

## Expected
- 컨텍스트 메뉴에 "코멘트 설정" 항목이 표시된다
