---
id: tc_71_file_name_click_preview
data_key: valid_user
priority: high
tags: [positive, files, preview]
type: structured
---
# 파일명 클릭 시 미리보기 또는 파일 상세 화면 표시

## Precondition
- 로그인 완료, 최근파일(/recents) 페이지, 파일(moomin1.jpg 등) 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 첫 번째 파일명(div.list-preview-name 또는 div.list__preview-name) 클릭
4. 미리보기 또는 파일 상세 화면 로드 대기

## Expected
- 클릭 후 파일 미리보기 모달 또는 상세 화면이 표시된다
- 페이지가 정상 반응한다 (오류 없음)
