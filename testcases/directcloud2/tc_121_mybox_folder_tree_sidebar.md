---
id: tc_121_mybox_folder_tree_sidebar
data_key: valid_user
priority: medium
tags: [positive, mybox, sidebar, folder-tree]
type: structured
---
# My Box 사이드바 폴더 트리 — 드롭존(item-dropzone) 항목 표시 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 폴더 트리 영역(#nav-tree-list 또는 .folder-tree-item) 가시성 확인

## Expected
- 폴더 트리 항목(.folder-tree-item)이 1개 이상 표시된다
- 폴더 트리 항목 중 현재 선택된 항목(.selected)이 표시된다
