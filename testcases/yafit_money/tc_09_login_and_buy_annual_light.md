---
id: tc_09
data_key: valid_user
priority: high
tags: [positive, auth, smoke]
type: structured
---
# 로그인 후 연간 라이트 결제 주문 페이지 이동

## Precondition
0. https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html 접속
0. 비로그인 상태
0. 연간 결제 탭 활성화 상태

## Steps
1. 라이트 플랜 "연간 결제하기" 버튼을 클릭한다.
2. 로그인 팝업 아이디 필드에 test_data[valid_user].username 입력한다.
3. 비밀번호 필드에 test_data[valid_user].password 입력한다.
4. "야나두 계정으로 로그인" 버튼을 클릭한다.

## Expected
- 로그인 성공 후 주문 상세 페이지로 이동되어야 한다.
- URL이 "https://www.yanadoo.co.kr/mypage/order/cart/detail/" 로 시작되어야 한다.
- "주문 상품" 섹션에 "[야핏사이클] 야핏사이클 라이트 플랜 (12개월 앱 이용권)" 상품명이 표시되어야 한다.
- "결제하기" 버튼이 표시되어야 한다.
