---
id: tc_224_mybox_file_info_panel
data_key: valid_user
priority: medium
tags: [positive, mybox, file-info, ui]
type: structured
---
# 마이박스 — 파일 선택 시 우측 정보 패널 표시 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행 단일 클릭 (선택)
4. 우측 파일 상세 정보 패널 표시 확인
5. 파일명, 크기, 날짜, 업로더 등 정보 표시 확인

## Expected
- 파일 선택 시 우측 정보 패널이 표시된다
- 파일 상세 정보(이름, 크기, 날짜 등)가 표시된다
