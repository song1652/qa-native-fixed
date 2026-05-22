---
id: tc_269_mybox_sidebar_folder_click
data_key: valid_user
priority: medium
tags: [positive, mybox, folder-tree, navigation]
type: structured
---
# 마이박스 — 사이드바 폴더 트리에서 폴더 클릭 시 파일 목록 변경 확인

## Precondition
- 로그인 완료, 마이박스에 하위 폴더 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 사이드바 폴더 트리에서 하위 폴더 클릭
4. 메인 영역의 파일 목록이 해당 폴더 내용으로 변경 확인

## Expected
- 사이드바 폴더 클릭 시 메인 파일 목록이 해당 폴더 내용으로 변경된다
