---
id: inventory-tc-02
title: 가격 낮은순 정렬
priority: medium
category: inventory
---

## 전제 조건
- standard_user / secret_sauce 로 로그인 가능

## 테스트 절차
1. https://www.saucedemo.com 접속 후 로그인
2. 정렬 드롭다운에서 "Price (low to high)" 선택

## 기대 결과
- 첫 번째 상품 가격이 두 번째 상품 가격보다 낮거나 같음
- 상품 순서가 변경됨 (가장 저렴한 상품 "$7.99" Sauce Labs Onesie가 상단에 위치)
