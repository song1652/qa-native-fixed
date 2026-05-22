---
id: tc_294_trash_file_path_column
data_key: valid_user
priority: low
tags: [positive, trash, ui, table]
type: structured
---
# 휴지통 — 파일 경로 컬럼 표시 확인

## Precondition
- 로그인 완료, 휴지통에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "휴지통"(li#trash) 클릭
3. 파일 목록에서 원본 경로 컬럼 확인

## Expected
- 삭제된 파일의 원본 경로가 목록에 표시된다
