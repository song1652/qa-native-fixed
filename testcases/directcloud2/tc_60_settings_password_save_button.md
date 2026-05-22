---
id: tc_60_settings_password_save_button
data_key: valid_user
priority: medium
tags: [negative, settings, password, validation]
type: structured
---
# 설정 모달 — 빈 비밀번호 입력 시 저장 버튼 동작 확인

## Precondition
- 로그인 완료, 비밀번호 변경 폼 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필(.nav-profile) 클릭 → "변경" 버튼 클릭
3. 비밀번호 필드 비운 채 "비밀번호 변경" 버튼(#btn-settings-password-save) 클릭

## Expected
- 빈 값 제출 시 비밀번호 변경이 진행되지 않는다 (모달 유지 또는 에러 표시)
- 설정 모달(#modal-settings)이 유지된다
