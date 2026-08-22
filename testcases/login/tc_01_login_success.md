---
id: login-tc-01
title: 정상 로그인 성공
priority: high
category: login
---

## 전제 조건
- https://www.saucedemo.com 접속 가능

## 테스트 절차
1. https://www.saucedemo.com 접속
2. Username 필드에 `standard_user` 입력
3. Password 필드에 `secret_sauce` 입력
4. "Login" 버튼 클릭

## 기대 결과
- URL이 `/inventory.html`로 이동
- 페이지 제목 "Swag Labs" 또는 상품 목록이 표시됨
- 로그인 에러 메시지가 없음
