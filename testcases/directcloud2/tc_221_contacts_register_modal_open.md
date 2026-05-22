---
id: tc_221_contacts_register_modal_open
data_key: valid_user
priority: medium
tags: [positive, contacts, register, modal]
type: structured
---
# 연락처 — 개별 등록 버튼 클릭 시 등록 폼 표시 확인

## Precondition
- 로그인 완료, 연락처 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "연락처"(li#contacts) 클릭
3. "등록" 버튼 클릭
4. 연락처 등록 폼/모달 오픈 확인
5. 이름, 이메일, 전화번호, 소속 입력 필드 존재 확인

## Expected
- 연락처 등록 폼이 열린다
- 이름, 이메일 주소, 전화번호, 소속 입력 필드가 표시된다
