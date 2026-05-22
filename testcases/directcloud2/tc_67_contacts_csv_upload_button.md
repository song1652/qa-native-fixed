---
id: tc_67_contacts_csv_upload_button
data_key: valid_user
priority: low
tags: [positive, contacts, csv, upload]
type: structured
---
# 주소록 — CSV 업로드 버튼 표시 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/contacts 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "주소록"(li#contacts) 클릭
3. "CSV 업로드" 버튼(button:has-text("CSV 업로드")) 가시성 확인

## Expected
- "CSV 업로드" 버튼이 표시된다
