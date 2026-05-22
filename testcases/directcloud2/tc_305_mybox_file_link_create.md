---
id: tc_305_mybox_file_link_create
data_key: valid_user
priority: high
tags: [positive, mybox, link, create, write]
type: structured
---
# 마이박스 — 파일 공유 링크 생성

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 우클릭 → "링크 생성" 메뉴 클릭
4. 링크 생성 모달에서 확인/생성 버튼 클릭
5. 생성된 링크 URL이 표시되는지 확인

## Expected
- 링크 생성 모달이 열린다
- 확인 클릭 후 공유 링크 URL이 생성되어 표시된다
