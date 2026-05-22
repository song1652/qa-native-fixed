---
id: tc_130_recents_file_checkbox_individual
data_key: valid_user
priority: medium
tags: [positive, recent, files, selection]
type: structured
---
# 최근파일 — 개별 파일 체크박스 선택 상태 전환 확인

## Precondition
- 로그인 완료, 최근파일(/recents) 페이지, 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 첫 번째 파일 체크박스(.checkbox-list-item) 클릭 (선택)
4. 체크 상태 확인
5. 체크박스 다시 클릭 (해제)
6. 해제 상태 확인

## Expected
- 체크박스 클릭 시 checked 상태가 된다
- 다시 클릭 시 unchecked 상태로 전환된다
