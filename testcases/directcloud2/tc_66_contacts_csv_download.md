---
id: tc_66_contacts_csv_download
data_key: valid_user
priority: low
tags: [positive, contacts, csv, download]
type: structured
---
# 주소록 — 개인 주소록 CSV 다운로드 버튼 표시 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/contacts 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "주소록"(li#contacts) 클릭
3. "개인 주소록 CSV 다운로드" 버튼(button:has-text("개인 주소록 CSV 다운로드")) 가시성 확인

## Expected
- CSV 다운로드 버튼(button.btn-box:has-text("개인 주소록 CSV 다운로드"))이 표시된다
