---
id: tc_35_breadcrumb_location_displayed
data_key: valid_user
priority: medium
tags: [positive, files, ui, breadcrumb]
type: structured
---
# 파일 목록 브레드크럼(현재 경로) 표시 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 파일 목록 페이지 로드 후 브레드크럼(.folder-location) 확인

## Expected
- 브레드크럼 영역(.folder-location)이 표시된다
- 현재 위치 텍스트(.text-location)가 표시된다
