---
id: tc_298_mybox_context_menu_all_items
data_key: valid_user
priority: medium
tags: [positive, mybox, context-menu]
type: structured
---
# 마이박스 — 파일 컨텍스트 메뉴 전체 항목 목록 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴 전체 항목 목록 확인

## Expected
- 미리보기, 다운로드, 이름 변경, 복사, 이동, 링크 생성, 메일 전송, 태그, 버전 이력, 기한 설정, 잠금, 이용 이력, 코멘트, 삭제 등 항목이 표시된다
