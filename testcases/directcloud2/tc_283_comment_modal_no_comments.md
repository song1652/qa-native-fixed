---
id: tc_283_comment_modal_no_comments
data_key: valid_user
priority: low
tags: [positive, comment, modal, empty-state]
type: structured
---
# 코멘트 모달 — 코멘트 없을 때 빈 상태 메시지 확인

## Precondition
- 로그인 완료, 코멘트 없는 파일 선택

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 코멘트 없는 파일 선택 후 코멘트 모달 오픈
4. 빈 상태 메시지 확인

## Expected
- 코멘트가 없을 때 "코멘트가 없습니다" 또는 유사한 빈 상태 메시지가 표시된다
