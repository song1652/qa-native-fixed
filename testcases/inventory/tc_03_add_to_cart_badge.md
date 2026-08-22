---
id: inventory-tc-03
title: 상품 추가 시 장바구니 배지 카운트 증가
priority: high
category: inventory
---

## 전제 조건
- standard_user / secret_sauce 로 로그인 가능

## 테스트 절차
1. https://www.saucedemo.com 접속 후 로그인
2. 첫 번째 상품의 "Add to cart" 버튼 클릭
3. 두 번째 상품의 "Add to cart" 버튼 클릭

## 기대 결과
- 장바구니 아이콘 배지에 숫자 "2" 표시
- 클릭한 버튼이 "Remove"로 변경됨
