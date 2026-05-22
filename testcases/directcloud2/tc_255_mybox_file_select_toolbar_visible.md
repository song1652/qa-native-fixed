---
id: tc_255_mybox_file_select_toolbar_visible
data_key: valid_user
priority: medium
tags: [positive, mybox, selection, toolbar]
type: structured
---
# 마이박스 — 파일 선택 시 액션 툴바 표시 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 체크박스 클릭 (1개 선택)
4. 상단 액션 툴바 표시 확인 (다운로드, 삭제, 이동, 복사 등 버튼)

## Expected
- 파일 선택 시 상단 툴바에 액션 버튼들이 표시된다
