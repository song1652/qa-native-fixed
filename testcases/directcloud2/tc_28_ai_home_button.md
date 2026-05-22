---
id: tc_28_ai_home_button
data_key: valid_user
priority: low
tags: [positive, ai, navigation]
type: structured
---
# AI Home 버튼 클릭 동작 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 헤더 AI Home 버튼(#showAIHome) 가시성 확인
3. AI Home 버튼(#showAIHome) 클릭

## Expected
- #showAIHome 버튼이 헤더에 표시된다
- 클릭 후 페이지가 정상적으로 반응한다 (오류 없음)
