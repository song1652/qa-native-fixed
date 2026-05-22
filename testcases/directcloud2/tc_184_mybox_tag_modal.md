---
id: tc_184_mybox_tag_modal
data_key: valid_user
priority: medium
tags: [positive, mybox, tag, modal]
type: structured
---
# 마이박스 — 파일 태그 모달 오픈 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행 우클릭 → 컨텍스트 메뉴에서 태그 관련 항목 클릭
4. 태그 모달(#modal-tag) 오픈 확인
5. 태그 입력 필드(#id-tag) 존재 확인

## Expected
- 태그 모달이 열린다
- 태그 입력 필드가 표시된다
