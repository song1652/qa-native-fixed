---
id: tc_07
data_key: null
priority: high
tags: [auth, negative, smoke]
type: structured
---
# 비로그인 결제하기 클릭 시 로그인 팝업 표시

## Precondition
0. https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html 접속
0. 비로그인(로그아웃) 상태

## Steps
1. 연간 결제 탭의 "연간 결제하기" 버튼을 클릭한다.

## Expected
- 로그인 팝업(iframe)이 표시되어야 한다.
- 아이디 입력 필드 "아이디를 입력해주세요." 가 표시되어야 한다.
- 비밀번호 입력 필드 "비밀번호를 입력해주세요." 가 표시되어야 한다.
- "야나두 계정으로 로그인" 버튼이 표시되어야 한다.
- 카카오, 네이버, 애플, 페이스북 소셜 로그인 버튼이 표시되어야 한다.
