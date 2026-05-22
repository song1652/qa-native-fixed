---
id: tc_307_sharedbox_file_comment_write
data_key: valid_user
priority: medium
tags: [positive, sharedbox, comment, write]
type: structured
---
# 공유박스 — Photo 폴더 파일에 코멘트 작성

## Precondition
- 로그인 완료
- Shared Box > Photo 폴더에 test_image.png 존재

## Steps
1. 유효한 자격증명으로 로그인
2. "Shared Box" 클릭
3. Photo 폴더 더블클릭하여 진입
4. test_image.png 클릭 → 우측 코멘트 패널 표시 확인
5. 코멘트 입력창(textarea-comments-top)에 텍스트 입력 (test_data: comment_text)
6. "확인" 버튼 클릭
7. 작성한 코멘트가 목록에 표시되는지 확인

## Expected
- Shared Box > Photo > test_image.png 클릭 시 우측 코멘트 패널이 표시된다
- 작성한 코멘트가 코멘트 목록에 표시된다
