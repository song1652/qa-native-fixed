---
id: tc_179_mybox_breadcrumb_navigation
data_key: valid_user
priority: medium
tags: [positive, mybox, navigation, breadcrumb]
type: structured
---
# 마이박스 — 폴더 진입 후 브레드크럼 네비게이션 확인

## Precondition
- 로그인 완료, 마이박스에 폴더 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 폴더 더블클릭하여 진입
4. 상단 브레드크럼에 폴더 경로 표시 확인
5. 브레드크럼의 상위 폴더 클릭
6. 상위 폴더로 이동 확인

## Expected
- 폴더 진입 시 브레드크럼에 경로가 표시된다
- 브레드크럼 클릭 시 해당 폴더로 이동된다
