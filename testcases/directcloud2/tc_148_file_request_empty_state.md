---
id: tc_148_file_request_empty_state
data_key: valid_user
priority: low
tags: [positive, file-request, empty-state]
type: structured
---
# 파일 요청 — 요청 없을 때 빈 상태 메시지 확인

## Precondition
- 로그인 완료, 파일 요청 0건

## Steps
1. 유효한 자격증명으로 로그인
2. "파일 요청"(li#file-requests) 클릭
3. 빈 상태 메시지 확인

## Expected
- 파일 요청이 없을 때 적절한 빈 상태 메시지가 표시된다
