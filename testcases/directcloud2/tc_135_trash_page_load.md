---
id: tc_135_trash_page_load
data_key: valid_user
priority: medium
tags: [positive, trash, navigation]
type: structured
---
# 휴지통 — 페이지 로드 및 파일 목록 표시 확인

## Precondition
- 로그인 완료
- 삭제된 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "휴지통"(li#trash) 클릭
3. 파일 목록 표시 확인

## Expected
- 휴지통 페이지가 로드된다
- 삭제된 파일 목록이 표시된다
