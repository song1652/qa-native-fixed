---
id: tc_201_logout_flow
data_key: valid_user
priority: high
tags: [positive, auth, logout]
type: structured
---
# 로그아웃 — 정상 로그아웃 후 로그인 페이지 이동 확인

## Precondition
- 로그인 완료 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 하단 프로필 또는 로그아웃 버튼 클릭
3. 로그아웃 확인
4. 로그인 페이지(https://web.directcloud.jp/login)로 이동 확인

## Expected
- 로그아웃 후 로그인 페이지로 리다이렉트된다
- 세션이 종료된다
