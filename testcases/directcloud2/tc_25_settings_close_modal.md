---
id: tc_25_settings_close_modal
data_key: valid_user
priority: medium
tags: [positive, settings, modal]
type: structured
---
# 설정 모달 닫기 (X 버튼)

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필 영역(.nav-profile) 클릭
3. 설정 모달(#modal-settings) 열림 확인
4. 모달 닫기 버튼(button.close) 클릭

## Expected
- 설정 모달이 닫힌다
- 메인 파일 목록 영역(#main)이 다시 표시된다
