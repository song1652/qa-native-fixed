---
id: tc_281_mybox_file_extension_filter
data_key: valid_user
priority: low
tags: [positive, mybox, filter, file-type]
type: structured
---
# 마이박스 — 파일 확장자별 필터링 기능 확인

## Precondition
- 로그인 완료, 마이박스에 다양한 확장자 파일 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 타입 필터 버튼 또는 드롭다운 클릭
4. 특정 확장자(예: PDF) 선택
5. 필터링 결과 확인

## Expected
- 선택한 확장자의 파일만 목록에 표시된다
