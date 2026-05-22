---
id: tc_59_settings_password_change_form
data_key: valid_user
priority: high
tags: [positive, settings, password]
type: structured
---
# 설정 모달 — 비밀번호 변경 폼 열기 및 입력 필드 확인

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필(.nav-profile) 클릭 → 설정 모달 오픈
3. "변경" 버튼(button:has-text("변경")) 클릭
4. 비밀번호 변경 폼의 password 입력 필드 3개 확인

## Expected
- 비밀번호 변경 폼이 표시된다
- 이전 비밀번호, 새 비밀번호, 비밀번호 확인 입력 필드(input[type="password"]) 3개가 표시된다
- "비밀번호 변경" 저장 버튼(#btn-settings-password-save)이 표시된다
