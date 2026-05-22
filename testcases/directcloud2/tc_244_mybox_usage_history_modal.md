---
id: tc_244_mybox_usage_history_modal
data_key: valid_user
priority: low
tags: [positive, mybox, history, modal]
type: structured
---
# 마이박스 — 파일 이용 이력 모달 내용 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행 우클릭 → 이용 이력 클릭
4. 이용 이력 모달 오픈 확인
5. 이용 이력 목록(날짜, 사용자, 작업 유형) 표시 확인

## Expected
- 이용 이력 모달이 열린다
- 날짜, 사용자, 작업 유형이 목록에 표시된다
