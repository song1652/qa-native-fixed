---
id: tc_232_nav_favorites_page
data_key: valid_user
priority: medium
tags: [positive, favorites, navigation]
type: structured
---
# 사이드바 — 즐겨찾기 메뉴 클릭 시 즐겨찾기 페이지 이동 확인

## Precondition
- 로그인 완료

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바에서 즐겨찾기(li#home 또는 별표 아이콘) 클릭
3. 즐겨찾기 페이지 로드 확인

## Expected
- 즐겨찾기 페이지가 로드된다
- 즐겨찾기 파일 목록 또는 빈 상태 메시지가 표시된다
