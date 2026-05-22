---
id: tc_206_mybox_folder_double_click_enter
data_key: valid_user
priority: medium
tags: [positive, mybox, folder, navigation]
type: structured
---
# 마이박스 — 폴더 더블클릭으로 진입 확인

## Precondition
- 로그인 완료, 마이박스에 폴더 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 폴더 행 더블클릭
4. 폴더 내부로 진입 확인
5. URL 또는 브레드크럼 변경 확인

## Expected
- 폴더 더블클릭 시 해당 폴더 내부로 진입된다
- 브레드크럼에 폴더 경로가 표시된다
