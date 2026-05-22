---
id: tc_243_mybox_file_lock_modal
data_key: valid_user
priority: medium
tags: [positive, mybox, lock, modal]
type: structured
---
# 마이박스 — 파일 잠금 확인 다이얼로그 표시 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행 우클릭 → 잠금 클릭
4. 잠금 확인 다이얼로그 또는 모달 표시 확인

## Expected
- 파일 잠금 확인 다이얼로그가 표시된다
- 확인/취소 버튼이 제공된다
