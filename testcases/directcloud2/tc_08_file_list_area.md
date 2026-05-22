---
id: tc_08_file_list_area
data_key: valid_user
priority: high
tags: [positive, smoke, files]
type: structured
---
# 로그인 후 파일/폴더 목록 영역 확인

## Precondition
- https://web.directcloud.jp/login 접속 후 정상 로그인 상태

## Steps
1. 유효한 자격증명으로 로그인 (tc_01 동일 절차)
2. 메인 파일 목록 영역 로드 대기

## Expected
- 메인 파일 목록 컨테이너(#main)가 표시된다
- 좌측 사이드바 폴더 트리(#nav)가 표시된다
- 현재 경로 브레드크럼(.folder-location)이 표시된다
