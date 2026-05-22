---
id: tc_172_settings_password_change
data_key: valid_user
priority: high
tags: [positive, settings, password]
type: structured
---
# 설정 모달 — 비밀번호 변경 폼 필드 확인

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필(.nav-profile) 클릭 → 설정 모달 오픈
3. 현재 비밀번호 입력 필드 존재 확인
4. 새 비밀번호 입력 필드 존재 확인
5. 비밀번호 확인 입력 필드 존재 확인
6. 저장 버튼(#btn-settings-password-save) 존재 확인

## Expected
- 현재 비밀번호, 새 비밀번호, 비밀번호 확인 필드가 표시된다
- 저장 버튼이 표시된다
