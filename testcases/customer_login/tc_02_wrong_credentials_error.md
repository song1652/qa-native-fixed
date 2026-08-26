---
id: CL-02
priority: High
data_key: serveone.login
tags: [login, error, customer]
---

# 고객 로그인 잘못된 자격증명 에러

## Precondition
0. 브라우저로 https://mall.serveone.co.kr/M3/cmm/login.dev 접속
0. 고객 로그인 섹션이 보이는 상태

## Steps
1. 고객 로그인 아이디 입력 필드에 존재하지 않는 아이디(예: invalid_test_user_99)를 입력한다
2. 고객 로그인 비밀번호 입력 필드에 잘못된 비밀번호(예: WrongPass!123)를 입력한다
3. 고객 로그인 영역의 "로그인" 버튼을 클릭한다

## Expected
- 로그인 실패 에러 메시지가 표시된다 (예: 아이디 또는 비밀번호를 확인해 주세요)
- 페이지 이동이 없고 로그인 페이지에 머문다
- 비밀번호 필드는 마스킹 상태를 유지한다
