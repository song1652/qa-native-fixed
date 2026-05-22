---
id: tc_72_file_list_preview_name_visible
data_key: valid_user
priority: medium
tags: [positive, files, ui]
type: structured
---
# 최근파일 목록에서 파일명 요소 표시 확인

## Precondition
- 로그인 완료, 최근파일(/recents) 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 파일명 요소(div.list-preview-name 또는 div.list__preview-name) 가시성 확인

## Expected
- 파일명 표시 요소가 최소 1개 이상 표시된다
- 파일명 텍스트가 비어있지 않다
