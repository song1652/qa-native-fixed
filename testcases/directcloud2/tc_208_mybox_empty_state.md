---
id: tc_208_mybox_empty_state
data_key: valid_user
priority: low
tags: [positive, mybox, empty-state]
type: structured
---
# 마이박스 — 빈 폴더 진입 시 빈 상태 메시지 확인

## Precondition
- 로그인 완료, 마이박스에 빈 폴더 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 비어있는 폴더 더블클릭으로 진입
4. 빈 상태 메시지 확인

## Expected
- 빈 폴더 진입 시 파일 없음 안내 메시지가 표시된다
