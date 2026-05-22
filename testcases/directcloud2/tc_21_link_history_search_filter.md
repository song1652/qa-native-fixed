---
id: tc_21_link_history_search_filter
data_key: valid_user
priority: medium
tags: [positive, link, search]
type: structured
---
# Link History 검색 필터 입력 및 검색 버튼 동작

## Precondition
- 로그인 완료, https://web.directcloud.jp/linkmanager 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "Link History" 메뉴(li#linkmanager) 클릭
3. 파일명/링크 검색 필드(input[placeholder="파일명 / 링크"])에 test_data[directcloud].search_keyword 입력
4. 검색 버튼(button:has-text("검색")) 클릭

## Expected
- 검색 입력 필드가 표시된다
- 키워드 입력 후 검색 버튼 클릭 시 페이지가 정상 반응한다
- 오류 없이 검색 결과 또는 빈 목록이 표시된다
