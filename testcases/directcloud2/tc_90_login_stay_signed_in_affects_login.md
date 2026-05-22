---
id: tc_90_login_stay_signed_in_affects_login
data_key: valid_user
priority: medium
tags: [positive, auth, checkbox]
type: structured
---
# Stay signed in 체크 해제 후 로그인 성공 여부 확인

## Precondition
- https://web.directcloud.jp/login 접속 상태

## Steps
1. 로그인 페이지 접속
2. Stay signed in 체크박스(input[type="checkbox"]) 클릭하여 해제
3. Company ID([name="company_code"])에 test_data[directcloud][valid_user].company 입력
4. User ID([name="id"])에 test_data[directcloud][valid_user].username 입력
5. Password([name="password"])에 test_data[directcloud][valid_user].password 입력
6. Login 버튼(#new_btn_login) 클릭

## Expected
- Stay signed in 체크 해제 상태에서도 로그인이 성공한다
- URL이 /mybox/ 형태로 변경된다
- #inputSearch가 표시된다
