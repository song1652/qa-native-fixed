---
id: tc_264_sharedbox_file_context_menu
data_key: valid_user
priority: medium
tags: [positive, sharedbox, context-menu, files]
type: structured
---
# 공유박스 — 파일 우클릭 컨텍스트 메뉴 항목 확인

## Precondition
- 로그인 완료, 공유박스 내 파일 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "공유박스"(li#sharedbox) 클릭
3. 파일이 있는 하위 폴더 진입
4. 파일 행 우클릭
5. 컨텍스트 메뉴 항목 확인

## Expected
- 공유박스 파일의 컨텍스트 메뉴가 표시된다
- 다운로드, 링크 생성 등 기본 항목이 포함된다
