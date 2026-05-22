---
id: tc_256_mybox_bulk_move
data_key: valid_user
priority: medium
tags: [positive, mybox, bulk, move]
type: structured
---
# 마이박스 — 파일 다중 선택 후 일괄 이동 버튼 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 2개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 체크박스 2개 클릭 (다중 선택)
4. 상단 툴바에 이동 버튼 표시 확인

## Expected
- 복수 파일 선택 시 상단 툴바에 이동 버튼이 표시된다
