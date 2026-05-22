---
id: tc_303_mybox_new_folder_create
data_key: valid_user
priority: high
tags: [positive, mybox, folder, create, write]
type: structured
---
# 마이박스 — 새 폴더 생성

## Precondition
- 로그인 완료, 마이박스 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 빈 공간 우클릭 또는 "새 폴더" 버튼 클릭
4. 폴더명 입력 필드에 폴더 이름 입력 (test_data: folder_name)
5. 확인 버튼 클릭 또는 Enter 키 입력
6. 생성된 폴더가 파일 목록에 표시되는지 확인

## Expected
- 입력한 이름으로 새 폴더가 생성된다
- 생성된 폴더가 마이박스 파일 목록에 표시된다
