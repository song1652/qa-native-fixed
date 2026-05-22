---
id: tc_112_notice_item_click
data_key: valid_user
priority: medium
tags: [positive, notice, navigation]
type: structured
---
# 공지 페이지 — 알림 항목 클릭 후 상세 내용 표시

## Precondition
- 로그인 완료, https://web.directcloud.jp/notice 페이지, 공지 항목 1개 이상 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "#goNotice" 버튼 클릭
3. 첫 번째 알림 항목 클릭
4. 상세 내용 또는 URL 변경 확인

## Expected
- 알림 항목 클릭 후 상세 내용이 표시되거나 상세 페이지로 이동한다
- 페이지가 오류 없이 반응한다
