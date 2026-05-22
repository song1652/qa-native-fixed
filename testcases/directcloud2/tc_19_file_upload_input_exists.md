---
id: tc_19_file_upload_input_exists
data_key: valid_user
priority: high
tags: [positive, files, upload]
type: structured
---
# 파일 업로드 input 요소 존재 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. My Box 페이지 로드 대기
3. 파일 업로드 input(#fileuploadBtn) DOM 존재 확인

## Expected
- 파일 업로드 input(#fileuploadBtn)이 DOM에 존재한다
- name 속성이 "Filedata"이다
- type이 "file"이다
