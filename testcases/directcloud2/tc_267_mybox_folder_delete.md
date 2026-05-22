---
id: tc_267_mybox_folder_delete
data_key: valid_user
priority: medium
tags: [positive, mybox, folder, delete]
type: structured
---
# 마이박스 — 폴더 삭제 컨텍스트 메뉴 항목 확인

## Precondition
- 로그인 완료, 마이박스에 폴더 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 폴더 행 우클릭 → "삭제" 클릭
4. 삭제 확인 다이얼로그 표시 확인

## Expected
- 폴더 삭제 항목이 컨텍스트 메뉴에 표시된다
- 삭제 확인 다이얼로그가 표시된다
