---
id: tc_207_mybox_navigate_up_button
data_key: valid_user
priority: medium
tags: [positive, mybox, navigation, folder]
type: structured
---
# 마이박스 — 상위 폴더 이동(뒤로가기) 확인

## Precondition
- 로그인 완료, 마이박스 서브 폴더 진입 상태

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 폴더 더블클릭으로 하위 폴더 진입
4. 브레드크럼에서 상위 폴더 클릭 또는 뒤로가기 버튼 클릭
5. 상위 폴더로 이동 확인

## Expected
- 상위 폴더로 이동된다
- 브레드크럼이 업데이트된다
