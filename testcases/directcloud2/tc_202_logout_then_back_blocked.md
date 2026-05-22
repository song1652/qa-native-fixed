---
id: tc_202_logout_then_back_blocked
data_key: valid_user
priority: high
tags: [negative, auth, logout, security]
type: structured
---
# 로그아웃 후 브라우저 뒤로가기 — 재접근 차단 확인

## Precondition
- 로그인 후 로그아웃 완료 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 로그아웃 실행
3. 브라우저 뒤로가기 버튼 클릭
4. 인증된 페이지 재접근 시도

## Expected
- 로그아웃 후 뒤로가기로 인증 페이지에 접근할 수 없다
- 로그인 페이지로 리다이렉트된다
