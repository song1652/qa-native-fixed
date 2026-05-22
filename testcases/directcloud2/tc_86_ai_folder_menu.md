---
id: tc_86_ai_folder_menu
data_key: valid_user
priority: low
tags: [positive, navigation, ai]
type: structured
---
# AI 폴더 메뉴(li#aihome) 클릭 후 페이지 반응 확인

## Precondition
- 로그인 완료 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 "AI 폴더"(li#aihome) 클릭
3. 페이지 반응 대기

## Expected
- 클릭 후 페이지가 정상 반응한다 (오류 없음)
- 파일 목록 영역(#main) 또는 관련 UI가 표시된다
