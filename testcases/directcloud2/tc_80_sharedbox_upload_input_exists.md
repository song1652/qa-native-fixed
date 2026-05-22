---
id: tc_80_sharedbox_upload_input_exists
data_key: valid_user
priority: medium
tags: [positive, shared, upload]
type: structured
---
# Shared Box — 파일 업로드 input 요소 존재 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/sharedbox/ 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "Shared Box"(li#sharedbox) 클릭
3. 파일 업로드 input(#fileuploadBtn) DOM 존재 확인

## Expected
- #fileuploadBtn 요소가 DOM에 존재한다
- Shared Box 내 파일 항목(.checkbox-list-item) 1개 이상이 존재한다
