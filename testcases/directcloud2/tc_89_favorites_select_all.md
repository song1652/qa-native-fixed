---
id: tc_89_favorites_select_all
data_key: valid_user
priority: low
tags: [positive, favorites, files, ui]
type: structured
---
# 즐겨찾기 페이지 — 전체선택 체크박스 클릭 동작

## Precondition
- 로그인 완료, https://web.directcloud.jp/favorites 페이지, 파일 1개 이상 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "즐겨찾기"(#nav li:has-text("즐겨찾기")) 클릭
3. 전체선택 체크박스(#ch_filesAll) 클릭
4. 체크 상태 확인

## Expected
- #ch_filesAll 체크박스가 표시된다
- 클릭 시 체크 상태로 전환된다
