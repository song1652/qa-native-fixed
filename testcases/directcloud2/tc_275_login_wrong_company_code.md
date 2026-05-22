---
id: tc_275_login_wrong_company_code
data_key: wrong_company
priority: high
tags: [negative, auth]
type: structured
---
# 잘못된 회사코드로 로그인 실패 확인

## Precondition
- https://web.directcloud.jp/login 접속 상태

## Steps
1. Company ID([name="company_code"])에 test_data[directcloud][wrong_company].company 입력
2. User ID([name="id"])에 test_data[directcloud][valid_user].username 입력
3. Password([name="password"])에 test_data[directcloud][valid_user].password 입력
4. Login 버튼(#new_btn_login) 클릭

## Expected
- 로그인에 실패한다
- URL이 https://web.directcloud.jp/login 에 그대로 유지된다
