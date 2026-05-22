---
id: tc_18_file_select_all_checkbox
data_key: valid_user
priority: medium
tags: [positive, files, ui]
type: structured
---
# 파일 전체선택 체크박스 동작 확인

## Precondition
- 로그인 완료 상태, 최근파일(/recents) 페이지 (파일 목록 존재)

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일" 메뉴(li#recents) 클릭
3. 전체선택 체크박스(#ch_filesAll) 가시성 확인
4. 전체선택 체크박스 클릭
5. 전체선택 후 상태 확인
6. 체크박스 다시 클릭하여 해제

## Expected
- #ch_filesAll 체크박스가 표시된다
- 클릭 시 체크 상태가 전환된다
