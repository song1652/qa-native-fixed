---
id: tc_169_mybox_folder_create
data_key: valid_user
priority: medium
tags: [positive, mybox, folder, create]
type: structured
---
# 마이박스 — 빈 공간 우클릭으로 새 폴더 생성 확인

## Precondition
- 로그인 완료, 마이박스 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 목록 빈 공간 우클릭
4. 컨텍스트 메뉴에서 "새 폴더" 항목 클릭
5. 폴더명 입력 후 확인

## Expected
- 새 폴더 생성 항목이 컨텍스트 메뉴에 표시된다
- 폴더명 입력 후 새 폴더가 생성된다
