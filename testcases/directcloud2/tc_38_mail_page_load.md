---
id: tc_38_mail_page_load
data_key: valid_user
priority: low
tags: [positive, mail, navigation]
type: structured
---
# Mail 페이지 로드 및 기본 UI 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/mail 접속

## Steps
1. 유효한 자격증명으로 로그인
2. "Mail" 메뉴(li#mail) 클릭
3. 페이지 로드 대기

## Expected
- URL이 /mail 로 변경된다
- 검색창(#inputSearch)이 표시된다
- 페이지가 오류 없이 로드된다
