---
id: tc_277_mybox_preview_modal_close
data_key: valid_user
priority: low
tags: [positive, mybox, preview, modal]
type: structured
---
# 마이박스 — 미리보기 모달 닫기 확인

## Precondition
- 로그인 완료, 미리보기 모달 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. "마이박스"(li#mybox) 클릭
3. 파일 클릭으로 미리보기 모달 오픈
4. 모달 닫기 버튼(X) 클릭
5. 모달 닫힘 확인

## Expected
- 미리보기 모달이 닫힌다
- 파일 목록으로 복귀된다
