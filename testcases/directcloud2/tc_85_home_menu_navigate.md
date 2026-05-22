---
id: tc_85_home_menu_navigate
data_key: valid_user
priority: medium
tags: [positive, navigation, home]
type: structured
---
# Home 메뉴 클릭 후 페이지 이동 확인

## Precondition
- 로그인 완료, 최근파일 등 다른 페이지에 있는 상태

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭으로 이동
3. "Home"(li#home) 클릭

## Expected
- 클릭 후 페이지가 변경된다 (URL 변경 또는 #main 내용 변화)
- 파일 목록 영역(#main)이 표시된다
