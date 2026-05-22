---
id: tc_36_search_in_recents
data_key: valid_user
priority: medium
tags: [positive, search, recent]
type: structured
---
# 최근파일 페이지에서 검색 기능 동작 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/recents 접속

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일" 메뉴(li#recents) 클릭
3. 검색창(#inputSearch)에 test_data[directcloud].search_keyword 입력
4. Enter 키 입력

## Expected
- 검색창에 키워드가 입력된다
- Enter 후 페이지가 검색 결과를 표시하거나 빈 목록을 표시한다 (오류 없음)
