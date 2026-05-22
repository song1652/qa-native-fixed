---
id: tc_173_settings_modal_close
data_key: valid_user
priority: low
tags: [positive, settings, modal]
type: structured
---
# 설정 모달 — 닫기 버튼으로 모달 닫힘 확인

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필(.nav-profile) 클릭 → 설정 모달 오픈
3. 모달 닫기 버튼(X) 클릭
4. 모달 닫힘 확인

## Expected
- 설정 모달이 닫힌다
- 메인 화면으로 복귀된다
