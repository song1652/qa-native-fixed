---
id: tc_246_login_empty_all_fields
data_key: valid_user
priority: medium
tags: [negative, auth, validation]
type: structured
---
# 로그인 — 모든 필드 비운 채 로그인 버튼 클릭 확인

## Precondition
- https://web.directcloud.jp/login 접속 상태

## Steps
1. 로그인 페이지 접속
2. 모든 입력 필드를 비운 채로 Login 버튼(#new_btn_login) 클릭

## Expected
- 로그인에 실패한다
- 로그인 페이지가 유지된다
