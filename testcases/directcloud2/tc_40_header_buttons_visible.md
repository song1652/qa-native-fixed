---
id: tc_40_header_buttons_visible
data_key: valid_user
priority: medium
tags: [positive, smoke, header, ui]
type: structured
---
# 로그인 후 헤더 주요 버튼 표시 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 헤더(#header) 가시성 확인
3. 주요 버튼 확인 — AI Home(#showAIHome), 알림(#goNotice), 코멘트 알림(#showNotifyComment)

## Expected
- #header가 표시된다
- #showAIHome 버튼이 표시된다
- #goNotice 버튼이 표시된다
- #showNotifyComment 버튼이 표시된다
