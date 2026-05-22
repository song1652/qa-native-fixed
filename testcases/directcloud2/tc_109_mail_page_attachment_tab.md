---
id: tc_109_mail_page_attachment_tab
data_key: valid_user
priority: medium
tags: [positive, mail, ui]
type: structured
---
# Mail 페이지 — "첨부파일" 탭 표시 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/mail 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "Mail"(li#mail) 클릭
3. "첨부파일" 탭 텍스트 요소 가시성 확인

## Expected
- URL이 /mail 로 변경된다
- "첨부파일" 텍스트를 포함한 탭 요소가 표시된다
