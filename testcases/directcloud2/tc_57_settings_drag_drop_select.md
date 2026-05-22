---
id: tc_57_settings_drag_drop_select
data_key: valid_user
priority: low
tags: [positive, settings, ui]
type: structured
---
# 설정 모달 — 드래그앤드롭 확인창 설정 select (사용/사용 안함) 확인

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필(.nav-profile) 클릭 → 설정 모달 오픈
3. 드래그앤드롭 확인창 select 요소 옵션 확인

## Expected
- 드래그앤드롭 select에 "사용" 옵션이 존재한다
- 드래그앤드롭 select에 "사용 안함" 옵션이 존재한다
