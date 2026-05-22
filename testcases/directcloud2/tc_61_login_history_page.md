---
id: tc_61_login_history_page
data_key: valid_user
priority: medium
tags: [positive, settings, login-history]
type: structured
---
# 로그인 이력 페이지 이동 및 기본 UI 확인

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필(.nav-profile) 클릭 → 설정 모달 오픈
3. "상세" 버튼(button:has-text("상세")) 클릭

## Expected
- URL이 https://web.directcloud.jp/login-history 로 변경된다
- 검색 버튼(button:has-text("검색"))이 표시된다
- 날짜 필터 입력 요소가 표시된다
