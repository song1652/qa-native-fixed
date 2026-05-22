---
id: tc_93_context_menu_link_create
data_key: valid_user
priority: high
tags: [positive, files, context-menu, link]
type: structured
---
# 파일 우클릭 → 링크생성 클릭 후 링크 생성 모달 표시 확인

## Precondition
- 로그인 완료, 최근파일(/recents) 페이지, 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 첫 번째 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴에서 "링크생성" 클릭
5. 링크 생성 모달 또는 링크 관련 UI 표시 대기

## Expected
- "링크생성" 클릭 후 링크 생성 관련 모달 또는 화면이 표시된다
- 페이지가 오류 없이 반응한다
