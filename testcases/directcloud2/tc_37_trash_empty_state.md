---
id: tc_37_trash_empty_state
data_key: valid_user
priority: low
tags: [positive, trash, ui]
type: structured
---
# 휴지통 페이지 로드 및 빈 상태 또는 목록 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/trash 접속

## Steps
1. 유효한 자격증명으로 로그인
2. "Trash" 메뉴(li#trash) 클릭
3. 페이지 로드 대기

## Expected
- URL이 /trash 로 변경된다
- 검색창(#inputSearch)이 표시된다
- 페이지가 오류 없이 로드된다 (#main 또는 body 가시성)
