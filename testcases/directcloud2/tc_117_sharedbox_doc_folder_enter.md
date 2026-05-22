---
id: tc_117_sharedbox_doc_folder_enter
data_key: valid_user
priority: medium
tags: [positive, shared, navigation, folder]
type: structured
---
# Shared Box — "Doc" 폴더 진입 및 파일 목록 확인

## Precondition
- 로그인 완료, Shared Box 페이지, "Doc" 폴더 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "Shared Box"(li#sharedbox) 클릭
3. "Doc" 폴더명(div.list-preview-name:has-text("Doc")) 클릭
4. 폴더 내 파일 목록 로드 대기

## Expected
- URL이 /sharedbox/ 하위 경로로 변경된다
- 파일 목록 영역(#main)이 표시된다
- 검색창(#inputSearch)이 유지된다
