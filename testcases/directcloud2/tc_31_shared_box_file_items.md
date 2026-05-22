---
id: tc_31_shared_box_file_items
data_key: valid_user
priority: high
tags: [positive, shared, files]
type: structured
---
# Shared Box 파일 항목 및 업로드 input 확인

## Precondition
- 로그인 완료, Shared Box 페이지

## Steps
1. 유효한 자격증명으로 로그인
2. "Shared Box" 메뉴(li#sharedbox) 클릭
3. 페이지 로드 대기
4. 파일 항목 체크박스(.checkbox-list-item) 및 업로드 input 확인

## Expected
- 최소 1개 이상의 파일 항목 체크박스(.checkbox-list-item)가 존재한다
- 파일 업로드 input(#fileuploadBtn)이 DOM에 존재한다
