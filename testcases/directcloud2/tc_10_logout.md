---
id: tc_10_logout
data_key: valid_user
priority: high
tags: [positive, smoke, auth]
type: structured
---
# 로그아웃 후 로그인 페이지 리다이렉트

## Precondition
- https://web.directcloud.jp/login 접속 후 정상 로그인 상태

## Steps
1. 유효한 자격증명으로 로그인 (tc_01 동일 절차)
2. 사이드바 프로필 영역(.nav-profile) 클릭
3. 로그아웃 버튼(button:has-text("로그아웃")) 대기 및 클릭

## Expected
- URL이 https://web.directcloud.jp/login 으로 리다이렉트된다
- Company ID 입력 필드([name="company_code"])가 다시 표시된다
