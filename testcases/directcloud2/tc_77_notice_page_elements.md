---
id: tc_77_notice_page_elements
data_key: valid_user
priority: medium
tags: [positive, notification, notice]
type: structured
---
# 공지/알림 페이지 — 알림 버튼 active 상태 및 검색창 표시 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/notice 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. 헤더 알림 버튼(#goNotice) 클릭
3. /notice 페이지 로드 후 알림 버튼(#goNotice) 상태 확인
4. 검색창(#inputSearch) 가시성 확인

## Expected
- URL이 /notice 로 변경된다
- #goNotice 버튼이 표시된다
- 검색창(#inputSearch)이 표시된다
