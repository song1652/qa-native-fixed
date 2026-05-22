---
id: tc_139_trash_mybox_tab
data_key: valid_user
priority: medium
tags: [positive, trash, filter, tab]
type: structured
---
# 휴지통 — 마이박스 탭 필터 확인

## Precondition
- 로그인 완료, 휴지통 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "휴지통"(li#trash) 클릭
3. "마이박스" 탭 클릭
4. 마이박스에서 삭제된 파일만 표시되는지 확인

## Expected
- 마이박스 탭 클릭 시 마이박스에서 삭제된 파일만 필터링된다
