---
id: tc_13_nav_shared_box
data_key: valid_user
priority: high
tags: [positive, navigation, shared]
type: structured
---
# Shared Box 메뉴 이동 및 파일 목록 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바에서 "Shared Box" 메뉴(li#sharedbox) 클릭

## Expected
- URL이 https://web.directcloud.jp/sharedbox/ 형태로 변경된다
- 전체선택 체크박스(#ch_filesAll)가 표시된다
- 파일 업로드 input(#fileuploadBtn)이 DOM에 존재한다
- 검색창(#inputSearch)이 유지된다
