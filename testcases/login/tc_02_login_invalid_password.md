---
id: login-tc-02
title: 잘못된 비밀번호 로그인 실패
priority: high
category: login
---

## 전제 조건
- https://www.saucedemo.com 접속 가능

## 테스트 절차
1. https://www.saucedemo.com 접속
2. Username 필드에 `standard_user` 입력
3. Password 필드에 `wrong_password` 입력
4. "Login" 버튼 클릭

## 기대 결과
- 로그인이 되지 않음 (URL 변경 없음)
- 에러 메시지 "Epic sadface: Username and password do not match any user in this service" 표시
- 에러 아이콘(X)이 Username/Password 필드에 표시됨
