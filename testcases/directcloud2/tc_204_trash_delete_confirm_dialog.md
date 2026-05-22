---
id: tc_204_trash_delete_confirm_dialog
data_key: valid_user
priority: high
tags: [positive, trash, delete, dialog]
type: structured
---
# 휴지통 — 영구삭제 클릭 시 확인 다이얼로그 표시 확인

## Precondition
- 로그인 완료, 휴지통에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "휴지통"(li#trash) 클릭
3. 파일 행 우클릭 → 컨텍스트 메뉴 오픈
4. "삭제" 클릭
5. 확인 다이얼로그 표시 확인

## Expected
- 영구삭제 클릭 시 확인 다이얼로그가 표시된다
- 취소 버튼이 제공되어 실수 방지가 가능하다
