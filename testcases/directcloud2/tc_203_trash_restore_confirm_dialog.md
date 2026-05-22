---
id: tc_203_trash_restore_confirm_dialog
data_key: valid_user
priority: high
tags: [positive, trash, restore, dialog]
type: structured
---
# 휴지통 — 복구 클릭 시 확인 다이얼로그 표시 확인

## Precondition
- 로그인 완료, 휴지통에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "휴지통"(li#trash) 클릭
3. 파일 행 우클릭 → 컨텍스트 메뉴 오픈
4. "복구" 클릭
5. 확인 다이얼로그 또는 모달 표시 확인

## Expected
- 복구 클릭 시 확인 다이얼로그가 표시된다
- 확인/취소 버튼이 제공된다
