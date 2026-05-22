---
id: tc_17_nav_trash
data_key: valid_user
priority: medium
tags: [positive, navigation, trash]
type: structured
---
# Trash 메뉴 이동 및 페이지 로드

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바에서 "Trash" 메뉴(li#trash) 클릭

## Expected
- URL이 https://web.directcloud.jp/trash 로 변경된다
- 검색창(#inputSearch)이 표시된다
- 페이지가 정상적으로 로드된다 (body 가시성)
