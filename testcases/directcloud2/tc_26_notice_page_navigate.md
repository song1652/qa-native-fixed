---
id: tc_26_notice_page_navigate
data_key: valid_user
priority: medium
tags: [positive, notification, navigation]
type: structured
---
# 알림(공지) 버튼 클릭 후 notice 페이지 이동

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 헤더 알림 버튼(#goNotice) 클릭

## Expected
- URL이 https://web.directcloud.jp/notice 로 변경된다
- 알림 버튼(#goNotice)이 헤더에 표시된다
- 검색창(#inputSearch)이 유지된다
