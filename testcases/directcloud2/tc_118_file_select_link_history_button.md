---
id: tc_118_file_select_link_history_button
data_key: valid_user
priority: medium
tags: [positive, files, link, selection]
type: structured
---
# 파일 선택 후 "링크이력" 버튼 표시 확인

## Precondition
- 로그인 완료, 최근파일(/recents) 페이지, 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 파일 체크박스(.checkbox-list-item) 1개 클릭 (선택 상태)
4. "링크이력" title을 가진 버튼 가시성 확인

## Expected
- 파일 선택 후 "링크이력" 버튼(title="링크이력")이 표시된다
