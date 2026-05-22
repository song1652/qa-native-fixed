---
id: tc_248_mybox_rename_inline
data_key: valid_user
priority: medium
tags: [positive, mybox, rename, inline]
type: structured
---
# 마이박스 — 파일 이름 변경 클릭 후 인라인 편집 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행 우클릭 → "이름 변경" 클릭
4. 인라인 편집 모드 진입 확인
5. 파일명 수정 후 Enter 입력
6. 변경된 파일명 표시 확인

## Expected
- 이름 변경 클릭 시 파일명이 편집 가능한 상태로 전환된다
- 변경 후 Enter 시 새 파일명이 반영된다
