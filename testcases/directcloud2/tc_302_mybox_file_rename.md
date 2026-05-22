---
id: tc_302_mybox_file_rename
data_key: valid_user
priority: high
tags: [positive, mybox, rename, write]
type: structured
---
# 마이박스 — 파일 이름 변경

## Precondition
- 로그인 완료, 마이박스에 이름 변경 가능한 파일 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 우클릭 → "이름 변경" 메뉴 클릭
4. 이름 입력 필드에 새 파일명 입력 (test_data: rename_filename)
5. Enter 키 또는 확인 버튼 클릭
6. 파일 목록에서 변경된 이름 확인

## Expected
- 입력한 새 이름으로 파일 이름이 변경된다
- 변경된 이름이 파일 목록에 즉시 반영된다
