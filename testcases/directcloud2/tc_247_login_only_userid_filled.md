---
id: tc_247_login_only_userid_filled
data_key: valid_user
priority: medium
tags: [negative, auth, validation]
type: structured
---
# 로그인 — User ID만 입력 후 로그인 시도 — 실패 확인

## Precondition
- https://web.directcloud.jp/login 접속 상태

## Steps
1. 로그인 페이지 접속
2. User ID([name="id"])에만 test_data[directcloud][valid_user].username 입력
3. Company ID, Password 비운 채 Login 버튼 클릭

## Expected
- 로그인 페이지(https://web.directcloud.jp/login) 유지
- 로그인에 실패한다
