---
id: "PL_02"
data_key: null
priority: "medium"
tags: ["general"]
type: structured
---
# 협력사 로그인 잘못된 자격증명 에러

## 사전 조건
브라우저로 https://mall.serveone.co.kr/M3/cmm/login.dev 접속
협력사 로그인 섹션이 보이는 상태

## Steps
페이지 상단의 "협력사 로그인" 탭을 클릭한다
협력사 로그인 아이디 입력 필드에 존재하지 않는 아이디(예: invalid_partner_99)를 입력한다
협력사 로그인 비밀번호 입력 필드에 잘못된 비밀번호(예: WrongPass!123)를 입력한다
협력사 로그인 영역의 "로그인" 버튼을 클릭한다

## Expected
"아이디 또는 패스워드를 확인하시기 바랍니다. 5번째 비밀번호 입력 실패 시, 5분뒤 로그인 가능합니다." 다이얼로그 팝업이 표시된다
페이지 이동이 없고 로그인 페이지에 머문다
