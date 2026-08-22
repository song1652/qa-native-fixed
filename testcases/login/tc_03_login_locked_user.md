---
id: login-tc-03
title: 잠긴 계정 로그인 시 에러 메시지
priority: medium
category: login
---

## 전제 조건
- https://www.saucedemo.com 접속 가능

## 테스트 절차
1. https://www.saucedemo.com 접속
2. Username 필드에 `locked_out_user` 입력
3. Password 필드에 `secret_sauce` 입력
4. "Login" 버튼 클릭

## 기대 결과
- 로그인이 되지 않음
- 에러 메시지 "Epic sadface: Sorry, this user has been locked out." 표시
