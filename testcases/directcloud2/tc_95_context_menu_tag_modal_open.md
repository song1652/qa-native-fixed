---
id: tc_95_context_menu_tag_modal_open
data_key: valid_user
priority: high
tags: [positive, files, context-menu, tag, modal]
type: structured
---
# 파일 우클릭 → 태그 클릭 후 태그 모달(#modal-tag) 표시 확인

## Precondition
- 로그인 완료, 최근파일(/recents) 페이지, 파일 최소 1개 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 첫 번째 파일 행(li.preview__list-item) 우클릭
4. 컨텍스트 메뉴에서 "태그" 클릭
5. 태그 모달(#modal-tag) 로드 대기

## Expected
- 태그 모달(#modal-tag)이 표시된다
- 태그 입력 필드(#id-tag, placeholder="tag")가 표시된다
- "확인" 버튼이 표시된다
