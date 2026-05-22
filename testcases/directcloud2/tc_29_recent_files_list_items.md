---
id: tc_29_recent_files_list_items
data_key: valid_user
priority: medium
tags: [positive, recent, files]
type: structured
---
# 최근파일 페이지 파일 항목 체크박스 존재 확인

## Precondition
- 로그인 완료, https://web.directcloud.jp/recents 접속

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일" 메뉴(li#recents) 클릭
3. 페이지 로드 대기
4. 파일 항목 체크박스(.checkbox-list-item) 존재 확인

## Expected
- URL이 /recents 로 변경된다
- 최소 1개 이상의 파일 항목 체크박스(.checkbox-list-item)가 존재한다
