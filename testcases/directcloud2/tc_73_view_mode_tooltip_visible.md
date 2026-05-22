---
id: tc_73_view_mode_tooltip_visible
data_key: valid_user
priority: low
tags: [positive, ui, view-mode]
type: structured
---
# 목록 보기/그리드 보기 전환 버튼 영역 표시 확인

## Precondition
- 로그인 완료, 파일 목록 페이지 (My Box 또는 최근파일)

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 보기 전환 영역(div.btn-view__tooltip 또는 "목록 보기" 텍스트 포함 요소) 확인

## Expected
- "목록 보기" 관련 UI 요소가 표시된다
