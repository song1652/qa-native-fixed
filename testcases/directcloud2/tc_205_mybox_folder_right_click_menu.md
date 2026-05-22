---
id: tc_205_mybox_folder_right_click_menu
data_key: valid_user
priority: medium
tags: [positive, mybox, folder, context-menu]
type: structured
---
# 마이박스 — 폴더 우클릭 컨텍스트 메뉴 항목 확인

## Precondition
- 로그인 완료, 마이박스에 폴더 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 폴더 행 우클릭
4. 컨텍스트 메뉴 항목 확인 (이름 변경, 삭제, 이동, 복사, 링크 생성 등)

## Expected
- 폴더 전용 컨텍스트 메뉴가 표시된다
- 파일과 동일 또는 유사한 기본 항목이 포함된다
