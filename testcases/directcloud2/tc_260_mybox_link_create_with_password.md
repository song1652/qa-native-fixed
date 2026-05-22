---
id: tc_260_mybox_link_create_with_password
data_key: valid_user
priority: medium
tags: [positive, mybox, link, password]
type: structured
---
# 마이박스 — 링크 생성 시 비밀번호 설정 필드 확인

## Precondition
- 로그인 완료, 링크 생성 모달 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 우클릭 → "링크 생성" 클릭
4. 링크 생성 모달에서 비밀번호 입력 필드 존재 확인
5. 비밀번호 입력

## Expected
- 링크 생성 모달에 비밀번호 설정 필드가 표시된다
- 비밀번호 입력이 가능하다
