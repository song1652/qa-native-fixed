---
id: tc_48_context_menu_favorite
data_key: valid_user
priority: medium
tags: [positive, files, context-menu, favorites]
type: structured
---
# 파일 우클릭 → 즐겨찾기 메뉴 항목 확인

## Precondition
- 로그인 완료, 최근파일(/recents) 페이지, 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 첫 번째 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴에서 "즐겨찾기" 항목 가시성 확인

## Expected
- 컨텍스트 메뉴에 "즐겨찾기" 항목이 표시된다
