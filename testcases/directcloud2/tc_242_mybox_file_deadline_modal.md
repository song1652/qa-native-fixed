---
id: tc_242_mybox_file_deadline_modal
data_key: valid_user
priority: medium
tags: [positive, mybox, deadline, modal]
type: structured
---
# 마이박스 — 파일 기한 설정 모달 내용 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행 우클릭 → 기한 설정 클릭
4. 기한 설정 모달 오픈 확인
5. 날짜 선택 UI 존재 확인

## Expected
- 기한 설정 모달이 열린다
- 날짜 선택 달력 또는 날짜 입력 필드가 표시된다
