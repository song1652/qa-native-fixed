---
id: tc_22
data_key: invalid_user
priority: medium
tags: [negative, auth, validation]
type: structured
---
# 잘못된 계정 정보 로그인 실패

## Precondition
0. https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html 접속
0. 비로그인 상태

## Steps
1. 네비게이션 "로그인" 버튼을 클릭하여 로그인 팝업을 연다.
2. 아이디 필드에 test_data[invalid_user].username 입력한다.
3. 비밀번호 필드에 test_data[invalid_user].password 입력한다.
4. "야나두 계정으로 로그인" 버튼을 클릭한다.

## Expected
- 로그인이 실패하고 오류 메시지가 표시되어야 한다.
- 로그인 팝업이 닫히지 않아야 한다.
- 주문 페이지로 이동되지 않아야 한다.
