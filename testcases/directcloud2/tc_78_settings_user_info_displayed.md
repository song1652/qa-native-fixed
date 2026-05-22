---
id: tc_78_settings_user_info_displayed
data_key: valid_user
priority: medium
tags: [positive, settings, profile]
type: structured
---
# 설정 모달 — 사용자 정보(회사명, 계정, 이메일, 용량) 표시 확인

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필(.nav-profile) 클릭 → 설정 모달 오픈
3. 모달 내 텍스트 확인 — 회사명(SampleLab), 계정(guest), 이메일, 용량

## Expected
- 설정 모달 내 회사명 또는 계정명(guest 포함 텍스트)이 표시된다
- 이메일 주소 형식 텍스트가 표시된다
- 용량 표시("%", "MB", "GB" 중 하나 포함)가 표시된다
