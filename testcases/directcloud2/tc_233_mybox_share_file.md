---
id: tc_233_mybox_share_file
data_key: valid_user
priority: medium
tags: [positive, mybox, share, context-menu]
type: structured
---
# 마이박스 — 파일 공유 컨텍스트 메뉴 항목 확인

## Precondition
- 로그인 완료, 마이박스에 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행 우클릭 → 컨텍스트 메뉴 오픈
4. 공유 관련 항목(공유, 메일로 공유 등) 존재 확인

## Expected
- 컨텍스트 메뉴에 공유 관련 항목이 표시된다
