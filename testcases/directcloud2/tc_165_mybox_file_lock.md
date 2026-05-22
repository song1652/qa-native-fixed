---
id: tc_165_mybox_file_lock
data_key: valid_user
priority: medium
tags: [positive, mybox, context-menu, lock]
type: structured
---
# 마이박스 — 파일 잠금 컨텍스트 메뉴 항목 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴에서 잠금 항목 존재 확인

## Expected
- 컨텍스트 메뉴에 파일 잠금 항목이 표시된다
