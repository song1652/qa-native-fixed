---
id: tc_231_mybox_favorite_add
data_key: valid_user
priority: medium
tags: [positive, mybox, favorites]
type: structured
---
# 마이박스 — 파일 즐겨찾기 추가 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행 우클릭 → 컨텍스트 메뉴 오픈
4. 즐겨찾기 추가 항목 클릭
5. 즐겨찾기 목록에 파일 추가 확인

## Expected
- 즐겨찾기 추가 항목이 컨텍스트 메뉴에 표시된다
- 파일이 즐겨찾기에 추가된다
