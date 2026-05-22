---
id: tc_142_contacts_table_columns
data_key: valid_user
priority: low
tags: [positive, contacts, ui, table]
type: structured
---
# 연락처 — 테이블 컬럼(이름/이메일/전화번호/소속/구분) 표시 확인

## Precondition
- 로그인 완료, 연락처(li#contacts) 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "연락처"(li#contacts) 클릭
3. 테이블 컬럼 헤더 확인 (이름, 이메일 주소, 전화번호, 소속, 구분)

## Expected
- 이름, 이메일 주소, 전화번호, 소속, 구분 컬럼 헤더가 표시된다
