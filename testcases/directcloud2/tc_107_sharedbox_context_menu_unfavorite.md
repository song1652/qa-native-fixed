---
id: tc_107_sharedbox_context_menu_unfavorite
data_key: valid_user
priority: low
tags: [positive, files, context-menu, favorites]
type: structured
---
# Shared Box 파일 우클릭 → 즐겨찾기 해제 메뉴 항목 확인

## Precondition
- 로그인 완료, Shared Box > DirectCloud AI 폴더, 즐겨찾기 등록된 파일 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "Shared Box"(li#sharedbox) → "DirectCloud AI" 폴더 클릭
3. 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴에서 "즐겨찾기 해제" 또는 "즐겨찾기" 항목 가시성 확인

## Expected
- 컨텍스트 메뉴에 "즐겨찾기 해제" 또는 "즐겨찾기" 항목이 표시된다
