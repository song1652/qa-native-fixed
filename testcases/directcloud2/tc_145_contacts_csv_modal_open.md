---
id: tc_145_contacts_csv_modal_open
data_key: valid_user
priority: medium
tags: [positive, contacts, csv, modal]
type: structured
---
# 연락처 — CSV 일괄등록 버튼 클릭 시 모달 오픈 확인

## Precondition
- 로그인 완료, 연락처 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "연락처"(li#contacts) 클릭
3. "CSV 일괄등록" 버튼 클릭
4. CSV 업로드 모달 오픈 확인
5. 파일 input 요소 존재 확인
6. "등록" 버튼 존재 확인
7. "닫기" 버튼 존재 확인

## Expected
- CSV 업로드 모달이 열린다
- 파일 input, 등록 버튼, 닫기 버튼이 표시된다
