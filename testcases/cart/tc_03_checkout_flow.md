---
id: cart-tc-03
title: 결제 플로우 완료
priority: high
category: cart
---

## 전제 조건
- standard_user / secret_sauce 로 로그인 가능

## 테스트 절차
1. https://www.saucedemo.com 접속 후 로그인
2. "Sauce Labs Backpack" "Add to cart" 클릭
3. 장바구니 아이콘 클릭
4. "Checkout" 버튼 클릭
5. First Name: "홍", Last Name: "길동", Zip/Postal Code: "12345" 입력
6. "Continue" 버튼 클릭
7. "Finish" 버튼 클릭

## 기대 결과
- "Thank you for your order!" 메시지 표시
- "Your order has been dispatched" 텍스트 표시
- "Back Home" 버튼 표시
