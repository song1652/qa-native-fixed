---
id: tc_309_mybox_file_deadline_set
data_key: valid_user
priority: medium
tags: [positive, mybox, deadline, write, date]
type: structured
---
# 마이박스 — 파일 기한 설정

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 우클릭 → "기한 설정" 메뉴 클릭
4. 날짜 선택 UI에서 미래 날짜 선택 (test_data: deadline_date)
5. 확인 버튼 클릭
6. 파일 행에 기한 표시 아이콘/날짜 표시 확인

## Expected
- 기한 설정 모달이 열린다
- 날짜 선택 후 확인 시 파일에 기한이 설정된다
- 파일 목록에 기한 관련 표시가 나타난다
