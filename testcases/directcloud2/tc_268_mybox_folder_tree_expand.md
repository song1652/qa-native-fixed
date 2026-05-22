---
id: tc_268_mybox_folder_tree_expand
data_key: valid_user
priority: low
tags: [positive, mybox, folder-tree, ui]
type: structured
---
# 마이박스 — 사이드바 폴더 트리 펼치기/접기 확인

## Precondition
- 로그인 완료, 마이박스에 하위 폴더 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 사이드바 폴더 트리에서 폴더 옆 화살표 클릭
4. 하위 폴더 목록 펼쳐짐 확인
5. 다시 클릭하여 접힘 확인

## Expected
- 폴더 트리의 화살표 클릭 시 하위 폴더가 펼쳐진다
- 다시 클릭 시 접힌다
