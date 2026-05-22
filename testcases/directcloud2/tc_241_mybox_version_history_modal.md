---
id: tc_241_mybox_version_history_modal
data_key: valid_user
priority: medium
tags: [positive, mybox, version, modal]
type: structured
---
# 마이박스 — 파일 버전 이력 모달 내용 확인

## Precondition
- 로그인 완료, 마이박스에 버전 이력 있는 파일 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 행 우클릭 → 버전 이력 클릭
4. 버전 이력 모달 오픈 확인
5. 버전 목록(버전번호, 날짜, 크기) 표시 확인

## Expected
- 버전 이력 모달이 열린다
- 버전 번호, 날짜, 파일 크기가 목록에 표시된다
