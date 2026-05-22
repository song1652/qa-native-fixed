---
id: tc_240_notice_detail_view
data_key: valid_user
priority: medium
tags: [positive, notice, detail]
type: structured
---
# 공지사항 — 공지 항목 클릭 시 상세 내용 표시 확인

## Precondition
- 로그인 완료, 공지사항 목록에 최소 1건 존재

## Steps
1. 유효한 자격증명으로 로그인
2. 공지사항 메뉴 클릭
3. 공지 항목 클릭
4. 공지 상세 내용 표시 확인

## Expected
- 공지 항목 클릭 시 상세 내용이 표시된다
- 제목, 내용, 날짜가 표시된다
