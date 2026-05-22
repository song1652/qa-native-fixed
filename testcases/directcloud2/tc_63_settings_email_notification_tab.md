---
id: tc_63_settings_email_notification_tab
data_key: valid_user
priority: low
tags: [positive, settings, email, notification]
type: structured
---
# 설정 모달 — 이메일 알림 탭 클릭 확인

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필(.nav-profile) 클릭 → 설정 모달 오픈
3. "이메일 알림" 탭 클릭(#modal-settings *:has-text("이메일 알림"))

## Expected
- 이메일 알림 탭이 클릭된다
- 설정 모달(#modal-settings)이 유지된다
