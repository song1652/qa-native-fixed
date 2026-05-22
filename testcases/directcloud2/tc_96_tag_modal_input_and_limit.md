---
id: tc_96_tag_modal_input_and_limit
data_key: valid_user
priority: medium
tags: [positive, files, tag, modal, validation]
type: structured
---
# 태그 모달 — 태그 입력창 존재 및 안내 문구 확인

## Precondition
- 로그인 완료, 태그 모달(#modal-tag) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) → 첫 번째 파일 우클릭 → "태그" 클릭
3. 태그 모달(#modal-tag) 표시 확인
4. 태그 안내 문구 텍스트 확인 ("최대 10글자" 또는 "10개" 포함)
5. 태그 입력 필드(#id-tag)에 "testtag" 입력 후 Enter

## Expected
- #modal-tag가 표시된다
- 안내 문구에 "10글자" 또는 "10개" 텍스트가 포함된다
- Enter 입력 시 태그가 추가된다 (또는 태그 목록에 반영)
- "확인" 버튼이 표시된다
