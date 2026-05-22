---
id: tc_11_nav_recent_files
data_key: valid_user
priority: high
tags: [positive, navigation, recent]
type: structured
---
# 최근파일 메뉴 이동 및 페이지 로드

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바에서 "최근파일" 메뉴(li#recents) 클릭

## Expected
- URL이 https://web.directcloud.jp/recents 로 변경된다
- 파일 목록 체크박스(#ch_filesAll)가 표시된다
- 검색창(#inputSearch)이 유지된다
