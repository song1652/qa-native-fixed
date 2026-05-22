---
id: tc_07_dashboard_layout
data_key: valid_user
priority: high
tags: [positive, smoke, ui]
type: structured
---
# 로그인 후 대시보드 레이아웃 확인

## Precondition
- https://web.directcloud.jp/login 접속 후 정상 로그인 상태

## Steps
1. 유효한 자격증명으로 로그인 (tc_01 동일 절차)
2. 로그인 완료 후 대시보드 페이지 로드 대기

## Expected
- URL에 "mybox"가 포함된다
- 상단 헤더(#header)가 표시된다
- 좌측 사이드바(#nav)가 표시된다
- 메인 파일 목록 영역(#main)이 표시된다
- 검색창(#inputSearch)이 표시된다
