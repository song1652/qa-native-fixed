---
id: tc_310_settings_profile_name_edit
data_key: valid_user
priority: medium
tags: [positive, settings, profile, write, edit]
type: structured
---
# 설정 — 프로필 표시 이름 수정

## Precondition
- 로그인 완료, 설정 모달 접근 가능

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필 영역(.nav-profile) 클릭 → 설정 모달 오픈
3. 프로필 이름 입력 필드 확인
4. 기존 이름 지우고 새 표시 이름 입력 (test_data: display_name)
5. 저장 버튼 클릭
6. 변경된 이름이 반영되는지 확인

## Expected
- 설정 모달의 프로필 이름 필드에 새 이름을 입력할 수 있다
- 저장 후 변경된 이름이 화면에 반영된다
