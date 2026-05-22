---
id: tc_266_mybox_folder_rename
data_key: valid_user
priority: medium
tags: [positive, mybox, folder, rename]
type: structured
---
# 마이박스 — 폴더 이름 변경 확인

## Precondition
- 로그인 완료, 마이박스에 폴더 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 폴더 행 우클릭 → "이름 변경" 클릭
4. 폴더명 수정 후 Enter
5. 변경된 폴더명 확인

## Expected
- 폴더 이름 변경 기능이 동작한다
- 변경된 폴더명이 목록에 반영된다
