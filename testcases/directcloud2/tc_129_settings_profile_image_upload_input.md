---
id: tc_129_settings_profile_image_upload_input
data_key: valid_user
priority: low
tags: [positive, settings, profile, upload]
type: structured
---
# 설정 모달 — 프로필 이미지 업로드 input 요소 존재 확인

## Precondition
- 로그인 완료, 설정 모달(#modal-settings) 열린 상태

## Steps
1. 유효한 자격증명으로 로그인
2. 사이드바 프로필(.nav-profile) 클릭 → 설정 모달 오픈
3. 프로필 이미지 업로드 input(#profileUploadBtn) DOM 존재 확인

## Expected
- #profileUploadBtn 요소가 DOM에 존재한다
- input type이 "file"이다
