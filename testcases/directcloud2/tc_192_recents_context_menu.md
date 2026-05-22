---
id: tc_192_recents_context_menu
data_key: valid_user
priority: medium
tags: [positive, recent, files, context-menu]
type: structured
---
# 최근파일 — 파일 우클릭 컨텍스트 메뉴 오픈 확인

## Precondition
- 로그인 완료, 최근파일 페이지, 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴 오픈 확인

## Expected
- 컨텍스트 메뉴가 표시된다
- 다운로드, 복사, 이동 등 기본 항목이 포함된다
