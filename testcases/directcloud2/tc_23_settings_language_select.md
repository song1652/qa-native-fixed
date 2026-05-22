---
id: tc_23_settings_language_select
data_key: valid_user
priority: low
tags: [positive, settings, language]
type: structured
---
# 설정 모달 언어 선택 옵션 확인

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필 영역(.nav-profile) 클릭
3. 설정 모달 내 언어 선택 select 요소 확인

## Expected
- 언어 선택 select가 표시된다
- 한국어, English, 日本語 옵션이 존재한다
