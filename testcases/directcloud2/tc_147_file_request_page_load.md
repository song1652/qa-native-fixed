---
id: tc_147_file_request_page_load
data_key: valid_user
priority: medium
tags: [positive, file-request, navigation]
type: structured
---
# 파일 요청 — 페이지 로드 및 컬럼 헤더 확인

## Precondition
- 로그인 완료

## Steps
1. 유효한 자격증명으로 로그인
2. "파일 요청"(li#file-requests) 클릭
3. 컬럼 헤더 확인 (받는 사람, 제목, 날짜, 파일수)

## Expected
- 파일 요청 페이지가 로드된다
- 받는 사람, 제목, 날짜, 파일수 컬럼이 표시된다
