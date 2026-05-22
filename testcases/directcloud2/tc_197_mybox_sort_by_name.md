---
id: tc_197_mybox_sort_by_name
data_key: valid_user
priority: low
tags: [positive, mybox, sort, ui]
type: structured
---
# 마이박스 — 파일 목록 이름 기준 정렬 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 2개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 목록 헤더의 "이름" 컬럼 클릭
4. 이름 오름차순 정렬 확인
5. 다시 클릭하여 내림차순 정렬 확인

## Expected
- 이름 컬럼 클릭 시 오름차순/내림차순으로 정렬된다
