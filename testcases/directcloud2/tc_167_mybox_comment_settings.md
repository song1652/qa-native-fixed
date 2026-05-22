---
id: tc_167_mybox_comment_settings
data_key: valid_user
priority: low
tags: [positive, mybox, context-menu, comment]
type: structured
---
# 마이박스 — 파일 코멘트 설정 컨텍스트 메뉴 항목 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴에서 코멘트 설정 항목 존재 확인

## Expected
- 컨텍스트 메뉴에 코멘트 설정 항목이 표시된다
