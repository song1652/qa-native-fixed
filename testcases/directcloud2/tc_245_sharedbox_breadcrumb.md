---
id: tc_245_sharedbox_breadcrumb
data_key: valid_user
priority: medium
tags: [positive, sharedbox, navigation, breadcrumb]
type: structured
---
# 공유박스 — 하위 폴더 진입 후 브레드크럼 표시 확인

## Precondition
- 로그인 완료, 공유박스에 하위 폴더 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "공유박스"(li#sharedbox) 클릭
3. 하위 폴더 더블클릭으로 진입
4. 브레드크럼에 경로 표시 확인
5. 브레드크럼 상위 폴더 클릭으로 이동 확인

## Expected
- 폴더 진입 시 브레드크럼에 경로가 표시된다
- 브레드크럼 클릭 시 상위 폴더로 이동된다
