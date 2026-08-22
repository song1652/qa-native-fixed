---
id: cart-tc-02
title: 장바구니에서 상품 제거
priority: medium
category: cart
---

## 전제 조건
- standard_user / secret_sauce 로 로그인 가능

## 테스트 절차
1. https://www.saucedemo.com 접속 후 로그인
2. "Sauce Labs Backpack" "Add to cart" 클릭
3. /cart.html 이동
4. "Remove" 버튼 클릭

## 기대 결과
- 장바구니가 비워짐 (상품 목록 없음)
- 장바구니 아이콘 배지 사라짐
