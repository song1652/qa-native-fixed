---
id: tc_127_login_only_company_filled
data_key: valid_user
priority: medium
tags: [negative, auth, validation]
type: structured
---
# 회사코드만 입력 후 로그인 시도 — 실패 확인

## Precondition
- https://web.directcloud.jp/login 접속 상태

## Steps
1. Company ID([name="company_code"])에만 test_data[directcloud][valid_user].company 입력
2. User ID, Password 비운 채 Login 버튼(#new_btn_login) 클릭

## Expected
- 로그인 페이지(https://web.directcloud.jp/login) 유지
- 로그인 폼 요소가 표시된다
