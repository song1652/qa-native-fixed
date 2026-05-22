---
id: tc_56_settings_menu_type_select
data_key: valid_user
priority: low
tags: [positive, settings, ui]
type: structured
---
# 설정 모달 — 메뉴 타입 select (리스트/트리) 옵션 확인

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필(.nav-profile) 클릭 → 설정 모달 오픈
3. 메뉴 타입 select 요소 옵션 확인

## Expected
- 메뉴 타입 select에 "리스트" 옵션이 존재한다
- 메뉴 타입 select에 "트리" 옵션이 존재한다
