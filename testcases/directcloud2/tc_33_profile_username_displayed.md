---
id: tc_33_profile_username_displayed
data_key: valid_user
priority: medium
tags: [positive, profile, ui]
type: structured
---
# 사이드바 프로필 영역 사용자명 표시 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필 영역(.nav-profile) 가시성 확인
3. 사용자명 표시 요소(.nav-profile h3) 텍스트 확인

## Expected
- 사이드바 프로필 영역(.nav-profile)이 표시된다
- 사용자명(.nav-profile h3) 텍스트가 표시된다 (비어있지 않음)
