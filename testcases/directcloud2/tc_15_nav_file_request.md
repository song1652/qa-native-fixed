---
id: tc_15_nav_file_request
data_key: valid_user
priority: medium
tags: [positive, navigation, file-request]
type: structured
---
# File Request 메뉴 이동 및 페이지 로드

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바에서 "File Request" 메뉴(li#file-requests) 클릭

## Expected
- URL이 https://web.directcloud.jp/file-requests 로 변경된다
- 검색창(#inputSearch)이 표시된다
- 전체선택 체크박스(#ch_filesAll)가 DOM에 존재한다
