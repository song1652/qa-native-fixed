---
id: tc_34_storage_usage_displayed
data_key: valid_user
priority: low
tags: [positive, profile, ui]
type: structured
---
# 스토리지 사용량 표시 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 스토리지 표시 요소(.nav-profile h4) 확인

## Expected
- 스토리지 사용량(.nav-profile h4)이 표시된다
- 텍스트에 "/" 또는 "MB"/"GB"가 포함된다 (용량 형식)
