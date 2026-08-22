---
id: cart-tc-01
title: 장바구니에 담은 상품 표시 확인
priority: high
category: cart
---

## 전제 조건
- standard_user / secret_sauce 로 로그인 가능

## 테스트 절차
1. https://www.saucedemo.com 접속 후 로그인
2. "Sauce Labs Backpack" 상품의 "Add to cart" 클릭
3. 장바구니 아이콘 클릭 (또는 /cart.html 이동)

## 기대 결과
- 장바구니에 "Sauce Labs Backpack" 상품이 표시됨
- 수량 "1", 가격 "$29.99" 표시
- "Remove" 버튼 존재
- "Continue Shopping" 버튼 존재
- "Checkout" 버튼 존재
