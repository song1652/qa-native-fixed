---
id: "CL_02"
data_key: null
priority: "medium"
tags: ["general"]
type: structured
---
# 고객 로그인 잘못된 자격증명 에러

## 사전 조건
브라우저로 https://mall.serveone.co.kr/M3/cmm/login.dev 접속
고객 로그인 섹션이 보이는 상태

## Steps
고객 로그인 아이디 입력 필드에 존재하지 않는 아이디(예: invalid_test_user_99)를 입력한다
고객 로그인 비밀번호 입력 필드에 잘못된 비밀번호(예: WrongPass!123)를 입력한다
고객 로그인 영역의 "로그인" 버튼을 클릭한다

## Expected
페이지 내 에러 메시지 영역(#LoginMsg)에 "사용자 ID 또는 패스워드가 정확하지 않습니다." 메시지가 표시된다
페이지 이동이 없고 로그인 페이지에 머문다
