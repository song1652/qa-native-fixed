---
id: tc_32_mybox_nav_click
data_key: valid_user
priority: medium
tags: [positive, navigation, mybox]
type: structured
---
# My Box 메뉴 클릭 후 파일 목록 화면 복귀

## Precondition
- 로그인 완료 상태, 다른 메뉴 선택 후 My Box 재클릭

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일" 메뉴(li#recents) 클릭하여 이동
3. "My Box" 메뉴(li#mybox) 클릭

## Expected
- URL이 https://web.directcloud.jp/mybox/ 형태로 변경된다
- 파일 목록 영역(#main)이 표시된다
- 파일 업로드 input(#fileuploadBtn)이 DOM에 존재한다
