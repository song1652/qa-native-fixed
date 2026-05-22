---
id: tc_128_login_only_password_filled
data_key: valid_user
priority: medium
tags: [negative, auth, validation]
type: structured
---
# 비밀번호만 입력 후 로그인 시도 — 실패 확인

## Precondition
- https://web.directcloud.jp/login 접속 상태

## Steps
1. Company ID, User ID는 비운 채
2. Password([name="password"])에만 test_data[directcloud][valid_user].password 입력
3. Login 버튼(#new_btn_login) 클릭

## Expected
- 로그인 페이지(https://web.directcloud.jp/login) 유지
- 로그인 폼 요소가 표시된다
