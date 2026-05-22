---
id: tc_289_login_form_field_order
data_key: valid_user
priority: low
tags: [positive, auth, ui, accessibility]
type: structured
---
# 로그인 페이지 — 입력 필드 탭 순서(Tab 키) 확인

## Precondition
- https://web.directcloud.jp/login 접속 상태

## Steps
1. 로그인 페이지 접속
2. Company ID 필드 클릭 후 Tab 키 입력
3. User ID 필드로 포커스 이동 확인
4. 다시 Tab 키 입력
5. Password 필드로 포커스 이동 확인
6. 다시 Tab 키 입력
7. Login 버튼으로 포커스 이동 확인

## Expected
- Tab 키로 Company ID → User ID → Password → Login 버튼 순서로 포커스가 이동된다
