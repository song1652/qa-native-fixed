---
id: tc_88_settings_language_change_english
data_key: valid_user
priority: low
tags: [positive, settings, language]
type: structured
---
# 설정 모달 — 언어를 English로 변경 후 select 값 확인

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필(.nav-profile) 클릭 → 설정 모달 오픈
3. 언어 select에서 "English" 옵션 선택
4. select 현재 값 확인

## Expected
- 언어 select에서 "English"를 선택할 수 있다
- select 값이 English에 해당하는 value로 변경된다
