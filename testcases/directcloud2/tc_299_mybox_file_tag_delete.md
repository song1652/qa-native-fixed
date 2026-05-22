---
id: tc_299_mybox_file_tag_delete
data_key: valid_user
priority: medium
tags: [positive, mybox, tag, delete]
type: structured
---
# 마이박스 — 파일 태그 삭제 확인

## Precondition
- 로그인 완료, 마이박스에 태그가 있는 파일 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 태그가 있는 파일 우클릭 → 태그 모달 오픈
4. 태그 목록에서 삭제 버튼(X) 클릭
5. 태그 삭제 확인

## Expected
- 태그 삭제 버튼 클릭 시 해당 태그가 제거된다
- 태그 목록에서 삭제된 태그가 사라진다
