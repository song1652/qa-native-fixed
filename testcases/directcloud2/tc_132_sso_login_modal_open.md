---
id: tc_132_sso_login_modal_open
data_key: valid_user
priority: medium
tags: [positive, auth, sso, modal]
type: structured
---
# SSO 로그인 버튼 클릭 시 모달 오픈 확인

## Precondition
- https://web.directcloud.jp/login 접속 상태

## Steps
1. "SSO 로그인" 버튼 클릭
2. 모달 오픈 확인
3. 회사코드 입력 필드 존재 확인
4. 확인 버튼 존재 확인

## Expected
- SSO 모달이 열린다
- 회사코드 입력 필드와 확인 버튼이 표시된다
