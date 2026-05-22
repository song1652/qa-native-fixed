---
id: tc_180_mybox_file_preview
data_key: valid_user
priority: high
tags: [positive, mybox, preview]
type: structured
---
# 마이박스 — 파일 클릭 시 미리보기 모달 열림 확인

## Precondition
- 로그인 완료, 마이박스에 미리보기 가능한 파일(이미지/PDF) 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 이미지 또는 PDF 파일 클릭
4. 미리보기 모달 오픈 확인

## Expected
- 파일 클릭 시 미리보기 모달이 열린다
- 파일 내용이 미리보기 영역에 표시된다
