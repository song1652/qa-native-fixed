---
id: tc_311_sharedbox_photo_folder_upload
data_key: valid_user
priority: high
tags: [positive, sharedbox, upload, image, photo]
type: structured
---
# 공유박스 — 포토 폴더에 이미지 파일 업로드

## Precondition
- 로그인 완료, 공유박스에 "photo" 또는 "Photo" 폴더 존재
- 업로드용 테스트 이미지 파일 준비 (tests/fixtures/test_image.png)

## Steps
1. 유효한 자격증명으로 로그인
2. "공유박스"(li#sharedbox) 클릭
3. "photo" 폴더 더블클릭으로 진입 (없으면 테스트 실패)
4. 파일 업로드 input(type=file)에 test_image.png 경로 주입
5. 업로드 완료 대기 (프로그레스바 사라짐 또는 파일명 표시)
6. 업로드된 이미지 파일이 목록에 표시되는지 확인

## Expected
- test_image.png가 공유박스의 photo 폴더에 업로드된다
- 업로드 후 파일 목록에 test_image.png가 표시된다
