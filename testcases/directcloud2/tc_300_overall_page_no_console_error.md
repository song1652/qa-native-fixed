---
id: tc_300_overall_page_no_console_error
data_key: valid_user
priority: medium
tags: [positive, ui, stability]
type: structured
---
# 전체 — 주요 페이지 접근 시 콘솔 오류 없음 확인

## Precondition
- 로그인 완료

## Steps
1. 유효한 자격증명으로 로그인
2. 마이박스, 최근파일, 공유박스, 휴지통, 연락처, 메일 페이지 순서대로 이동
3. 각 페이지에서 브라우저 콘솔 오류 없음 확인

## Expected
- 각 페이지 이동 시 브라우저 콘솔에 JavaScript 오류가 발생하지 않는다
