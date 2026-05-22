---
id: tc_79_mybox_upload_input_type_file
data_key: valid_user
priority: high
tags: [positive, files, upload]
type: structured
---
# My Box — 파일 업로드 input 속성 검증 (type=file, name=Filedata)

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. My Box 페이지 로드 후 파일 업로드 input(#fileuploadBtn) 속성 확인

## Expected
- #fileuploadBtn 요소가 DOM에 존재한다
- input type이 "file"이다
- input name이 "Filedata"이다
- form#fileupload가 DOM에 존재한다
