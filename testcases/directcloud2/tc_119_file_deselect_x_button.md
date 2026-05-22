---
id: tc_119_file_deselect_x_button
data_key: valid_user
priority: low
tags: [positive, files, selection, ui]
type: structured
---
# 파일 선택 후 X(선택 해제) 버튼으로 선택 취소

## Precondition
- 로그인 완료, 최근파일(/recents) 페이지, 파일 선택 상태

## Steps
1. 유효한 자격증명으로 로그인
2. "최근파일"(li#recents) 클릭
3. 첫 번째 파일 체크박스(.checkbox-list-item) 클릭 (선택 상태)
4. 선택 해제 버튼(button.sc-fQkuQJ.bFKmDS 또는 "×" 텍스트 버튼) 클릭
5. 선택 해제 확인

## Expected
- "×" 선택 해제 버튼이 표시된다
- 클릭 후 파일 선택이 해제된다
