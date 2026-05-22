---
id: tc_234_mybox_mail_send_context
data_key: valid_user
priority: medium
tags: [positive, mybox, mail, context-menu]
type: structured
---
# 마이박스 — 파일 메일 전송 컨텍스트 메뉴 → 메일 작성 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행 우클릭 → 컨텍스트 메뉴 오픈
4. "메일로 전송" 항목 클릭
5. 메일 작성 모달 또는 페이지 오픈 확인

## Expected
- 메일 전송 항목 클릭 시 메일 작성 화면이 열린다
- 첨부 파일로 선택한 파일이 포함된다
