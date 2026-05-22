---
id: tc_39_sidebar_all_menus_visible
data_key: valid_user
priority: medium
tags: [positive, smoke, navigation, ui]
type: structured
---
# 로그인 후 사이드바 전체 메뉴 항목 표시 확인

## Precondition
- 로그인 완료 상태 (https://web.directcloud.jp/mybox/MQ==)

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바(#nav) 가시성 확인
3. 각 메뉴 항목 존재 확인 — Home(li#home), 최근파일(li#recents), My Box(li#mybox), Shared Box(li#sharedbox), Trash(li#trash)

## Expected
- li#home, li#recents, li#mybox, li#sharedbox, li#trash 가 모두 표시된다
- 사이드바(#nav)가 표시된다
