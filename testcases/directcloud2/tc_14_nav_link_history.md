---
id: tc_14_nav_link_history
data_key: valid_user
priority: medium
tags: [positive, navigation, link]
type: structured
---
# Link History 메뉴 이동 및 검색 필터 UI 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바에서 "Link History" 메뉴(li#linkmanager) 클릭

## Expected
- URL이 https://web.directcloud.jp/linkmanager 로 변경된다
- 검색 필터 select 요소(select.form-control)가 표시된다
- 파일명/링크 검색 텍스트 필드(input[placeholder="파일명 / 링크"])가 표시된다
- 검색 버튼(button:has-text("검색"))이 표시된다
