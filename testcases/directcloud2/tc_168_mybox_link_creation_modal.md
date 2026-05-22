---
id: tc_168_mybox_link_creation_modal
data_key: valid_user
priority: medium
tags: [positive, mybox, context-menu, link, modal]
type: structured
---
# 마이박스 — 링크 생성 컨텍스트 메뉴 → 모달 옵션 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴에서 "링크 생성" 클릭
5. 링크 생성 모달 오픈 확인
6. 비밀번호, 만료일, 다운로드 횟수 등 옵션 필드 존재 확인

## Expected
- 링크 생성 모달이 열린다
- 링크 옵션(비밀번호, 만료일, 다운로드 횟수 등) 설정 필드가 표시된다
