---
id: tc_301_mybox_file_comment_write
data_key: valid_user
priority: high
tags: [positive, mybox, comment, write]
type: structured
---
# 마이박스 — 파일에 코멘트 작성

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 우클릭 → 코멘트 메뉴 클릭 (또는 우측 패널 코멘트 탭 클릭)
4. 코멘트 입력창에 테스트 텍스트 입력 (test_data: comment_text)
5. 전송 버튼 클릭 또는 Enter 입력
6. 작성한 코멘트가 목록에 표시되는지 확인

## Expected
- 입력한 코멘트 텍스트가 코멘트 목록에 표시된다
