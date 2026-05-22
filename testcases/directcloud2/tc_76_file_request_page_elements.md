---
id: tc_76_file_request_page_elements
data_key: valid_user
priority: medium
tags: [positive, file-request, ui]
type: structured
---
# File Request 페이지 — 전체선택 체크박스 및 검색창 표시 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/file-requests 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "File Request"(li#file-requests) 클릭
3. 전체선택 체크박스(#ch_filesAll) 및 검색창(#inputSearch) 가시성 확인

## Expected
- URL이 /file-requests 로 변경된다
- 전체선택 체크박스(#ch_filesAll)가 DOM에 존재한다
- 검색창(#inputSearch)이 표시된다
