---
id: tc_229_mybox_link_type_filter_direct
data_key: valid_user
priority: low
tags: [positive, mybox, link-history, filter]
type: structured
---
# 링크 이력 — 타입별 필터: 직접 링크 확인

## Precondition
- 로그인 완료, 마이박스 파일 선택, 링크 이력 모달 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 선택 후 링크 이력 버튼 클릭
4. 링크 타입 필터에서 "직접 링크" 선택
5. 필터 결과 확인

## Expected
- 직접 링크 타입 이력만 필터링되어 표시된다
