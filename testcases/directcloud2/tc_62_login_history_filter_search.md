---
id: tc_62_login_history_filter_search
data_key: valid_user
priority: low
tags: [positive, settings, login-history, search]
type: structured
---
# 로그인 이력 — 날짜 필터 select 및 검색 버튼 동작 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/login-history 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. 설정 모달 → "상세" 버튼 클릭 → /login-history 이동
3. 날짜 필터 select 요소 옵션 확인
4. 검색 버튼(button:has-text("검색")) 클릭

## Expected
- 날짜 필터 select 요소가 표시된다
- 검색 버튼 클릭 후 페이지가 정상 반응한다 (오류 없음)
