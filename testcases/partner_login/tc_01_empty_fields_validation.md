---
id: PL-01
priority: High
data_key: serveone.login
tags: [login, validation, partner]
---

# 협력사 로그인 빈 필드 유효성 검증

## Precondition
0. 브라우저로 https://mall.serveone.co.kr/M3/cmm/login.dev 접속
0. 협력사 로그인 섹션이 보이는 상태

## Steps
1. 협력사 로그인 아이디 입력 필드를 비워둔다
2. 협력사 로그인 비밀번호 입력 필드를 비워둔다
3. 협력사 로그인 영역의 "로그인" 버튼을 클릭한다

## Expected
- 로그인이 차단되거나 에러 메시지(아이디를 입력하세요 / 비밀번호를 입력하세요 등)가 표시된다
- 페이지 이동이 없고 로그인 페이지에 머문다
