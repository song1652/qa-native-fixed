---
id: tc_92_context_menu_rename_inline
data_key: valid_user
priority: medium
tags: [positive, files, context-menu, rename]
type: structured
---
# 파일 우클릭 → 이름변경 클릭 후 인라인 편집 활성화 확인

## Precondition
- 로그인 완료, 최근파일(/recents) 페이지, 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 첫 번째 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴에서 "이름변경"(.menu-이름변경-wrap) 클릭
5. 인라인 편집 입력창 또는 파일명 편집 상태 확인

## Expected
- "이름변경" 클릭 후 파일명 편집 모드가 활성화된다
- 파일명 입력 필드 또는 인라인 편집 요소가 표시된다
