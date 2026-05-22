---
id: tc_41_context_menu_appears
data_key: valid_user
priority: high
tags: [positive, files, context-menu]
type: structured
---
# 파일 우클릭 시 컨텍스트 메뉴 표시

## Precondition
- 로그인 완료, 최근파일(/recents) 페이지, 파일 항목 최소 1개 이상 존재

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 "최근파일"(li#recents) 클릭
3. 첫 번째 파일 행(li.preview__list-item) 우클릭

## Expected
- 우클릭 컨텍스트 메뉴가 표시된다
- 메뉴에 "이름바꾸기", "다운로드", "삭제" 항목이 포함된다
