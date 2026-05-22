---
id: tc_185_mybox_tag_add
data_key: valid_user
priority: medium
tags: [positive, mybox, tag]
type: structured
---
# 마이박스 — 파일에 태그 추가 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재, 태그 모달 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 태그 모달 오픈
4. 태그 입력 필드(#id-tag)에 태그명 입력
5. 태그 추가 버튼 클릭 또는 Enter 입력
6. 태그 추가 확인

## Expected
- 입력한 태그가 파일에 추가된다
- 태그 목록에 새 태그가 표시된다
