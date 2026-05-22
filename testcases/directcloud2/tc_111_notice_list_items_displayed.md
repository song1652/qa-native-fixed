---
id: tc_111_notice_list_items_displayed
data_key: valid_user
priority: medium
tags: [positive, notice, ui]
type: structured
---
# 공지 페이지 — 알림 목록 항목 표시 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/notice 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "#goNotice" 버튼 클릭
3. 알림 목록 항목 개수 확인

## Expected
- URL이 /notice 로 변경된다
- 알림 목록 항목이 1개 이상 표시된다
- 각 항목에 제목 텍스트가 포함된다
