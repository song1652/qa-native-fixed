---
id: tc_30_favorites_file_listed
data_key: valid_user
priority: medium
tags: [positive, favorites, files]
type: structured
---
# 즐겨찾기 페이지 파일 항목 존재 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/favorites 접속

## Steps
1. 유효한 자격증명으로 로그인
2. "즐겨찾기" 메뉴(#nav li:has-text("즐겨찾기")) 클릭
3. 페이지 로드 대기
4. 파일 항목 체크박스(.checkbox-list-item) 존재 확인

## Expected
- URL이 /favorites 로 변경된다
- 최소 1개 이상의 파일 항목 체크박스(.checkbox-list-item)가 존재한다
