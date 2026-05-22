---
id: tc_136_trash_file_columns
data_key: valid_user
priority: low
tags: [positive, trash, ui]
type: structured
---
# 휴지통 — 파일 목록 컬럼(이름/크기/날짜/확장자/경로) 확인

## Precondition
- 로그인 완료
- 휴지통에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "휴지통"(li#trash) 클릭
3. 파일 목록 컬럼 헤더 확인 (이름, 크기, 날짜, 확장자, 경로)

## Expected
- 이름, 크기, 날짜, 확장자, 경로 컬럼이 표시된다
