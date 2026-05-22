---
id: tc_152_notice_category_incident
data_key: valid_user
priority: low
tags: [positive, notice, category]
type: structured
---
# 공지사항 — 구분: 장애정보 항목 표시 확인

## Precondition
- 로그인 완료, 공지사항 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. 공지사항 메뉴 클릭
3. 구분 컬럼에서 "장애정보" 타입 공지 존재 여부 확인

## Expected
- 구분 컬럼에 "장애정보" 타입이 표시되거나, 업데이트/장애정보 구분 필터가 존재한다
