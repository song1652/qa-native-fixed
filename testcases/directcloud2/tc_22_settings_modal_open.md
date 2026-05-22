---
id: tc_22_settings_modal_open
data_key: valid_user
priority: high
tags: [positive, settings, modal]
type: structured
---
# 설정 모달 열기 및 주요 설정 항목 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필 영역(.nav-profile) 클릭
3. 설정 모달(#modal-settings) 표시 대기

## Expected
- 설정 모달(#modal-settings)이 표시된다
- 모달 내 비밀번호 변경 버튼(button:has-text("변경"))이 표시된다
- 로그아웃 버튼(button:has-text("로그아웃"))이 표시된다
- 언어 선택 select 요소가 표시된다
