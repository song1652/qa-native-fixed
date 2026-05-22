---
id: tc_293_recents_sort_by_date
data_key: valid_user
priority: low
tags: [positive, recent, sort, ui]
type: structured
---
# 최근파일 — 날짜 기준 정렬 확인

## Precondition
- 로그인 완료, 최근파일 페이지, 파일 최소 2개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 날짜 컬럼 헤더 클릭
4. 날짜 기준 정렬 확인

## Expected
- 날짜 컬럼 클릭 시 날짜 순으로 파일 목록이 정렬된다
