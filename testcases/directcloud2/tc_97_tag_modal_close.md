---
id: tc_97_tag_modal_close
data_key: valid_user
priority: low
tags: [positive, files, tag, modal]
type: structured
---
# 태그 모달 — X 버튼으로 닫기

## Precondition
- 로그인 완료, 태그 모달(#modal-tag) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) → 첫 번째 파일 우클릭 → "태그" 클릭
3. 태그 모달(#modal-tag) 표시 확인
4. 닫기 버튼(button.close) 클릭

## Expected
- 태그 모달이 닫힌다
- 파일 목록(li.preview__list-item)이 표시 상태를 유지한다
