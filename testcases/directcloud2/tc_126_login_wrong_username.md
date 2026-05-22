---
id: tc_126_login_wrong_username
data_key: invalid_user
priority: high
tags: [negative, auth]
type: structured
---
# 잘못된 User ID로 로그인 실패

## Precondition
- https://web.directcloud.jp/login 접속 상태

## Steps
1. Company ID([name="company_code"])에 test_data[directcloud][valid_user].company 입력
2. User ID([name="id"])에 test_data[directcloud][invalid_user].username 입력
3. Password([name="password"])에 test_data[directcloud][valid_user].password 입력
4. Login 버튼(#new_btn_login) 클릭

## Expected
- URL이 https://web.directcloud.jp/login 에 그대로 유지된다
- 로그인에 실패한다
