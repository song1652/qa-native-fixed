---
id: tc_235_session_check_after_reload
data_key: valid_user
priority: medium
tags: [positive, auth, session]
type: structured
---
# 세션 유지 — 페이지 새로고침 후 로그인 상태 유지 확인

## Precondition
- 로그인 완료 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 로그인 후 마이박스 페이지 확인
3. 브라우저 새로고침(F5 또는 Ctrl+R)
4. 로그인 상태 유지 여부 확인

## Expected
- 새로고침 후에도 로그인 상태가 유지된다
- 마이박스 페이지가 다시 표시된다
