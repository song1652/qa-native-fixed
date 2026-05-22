---
id: tc_24_settings_start_menu_select
data_key: valid_user
priority: low
tags: [positive, settings, ui]
type: structured
---
# 설정 모달 시작메뉴 select 옵션 확인

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필 영역(.nav-profile) 클릭
3. 설정 모달 내 시작메뉴 select 요소 옵션 확인

## Expected
- 시작메뉴 select 요소가 표시된다
- 최근파일, Home, My Box, Shared Box 옵션 중 하나 이상 존재한다
