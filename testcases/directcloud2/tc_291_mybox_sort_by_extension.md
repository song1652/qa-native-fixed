---
id: tc_291_mybox_sort_by_extension
data_key: valid_user
priority: low
tags: [positive, mybox, sort, ui]
type: structured
---
# 마이박스 — 파일 목록 확장자 기준 정렬 확인

## Precondition
- 로그인 완료, 마이박스에 다양한 확장자 파일 최소 2개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 목록 헤더의 "확장자" 컬럼 클릭
4. 확장자 기준 정렬 확인

## Expected
- 확장자 컬럼 클릭 시 확장자 순으로 파일 목록이 정렬된다
