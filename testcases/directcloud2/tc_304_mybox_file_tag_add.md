---
id: tc_304_mybox_file_tag_add
data_key: valid_user
priority: high
tags: [positive, mybox, tag, create, write]
type: structured
---
# 마이박스 — 파일에 태그 추가

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 우클릭 → "태그" 메뉴 클릭 (또는 우측 패널 태그 탭)
4. 태그 입력 필드에 태그명 입력 (test_data: tag_name)
5. 추가 버튼 클릭 또는 Enter 키 입력
6. 추가된 태그가 표시되는지 확인

## Expected
- 입력한 태그명이 파일 태그 목록에 추가된다
- 태그가 파일 행 또는 우측 패널에 표시된다
