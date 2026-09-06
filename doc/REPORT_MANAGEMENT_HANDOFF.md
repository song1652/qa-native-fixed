# 리포트 관리 UI 작업 인계

## 현재 상태

- 사용자 디자인 승인 완료.
- 운영 리포트 UI와 서버 삭제 API는 아직 수정하지 않음.
- 승인용 HTML 시안: `design-previews/report-list-proposal.html`
- 사용자가 터미널을 다시 열기 위해 구현 시작 전 중단을 요청함.

## 승인된 디자인

- 프로젝트의 기존 네이비·퍼플 디자인 토큰을 사용한다.
- 데스크톱은 좌측 리포트 목록, 우측 리포트 미리보기의 분할 레이아웃으로 구성한다.
- 모바일은 목록 위, 미리보기 아래의 단일 열로 전환한다.
- 상단에 검색, 최신순/오래된순/파일명순 정렬, 새로고침, 선택 삭제를 둔다.
- 각 리포트 행에 체크박스를 표시한다.
- 전체 선택 체크박스와 선택 개수 표시를 제공한다.
- 각 행에 열기, 새 탭, 개별 삭제 액션을 제공한다.
- 삭제 전 확인 모달을 표시한다.
- 현재 미리보기 중인 리포트를 삭제하면 미리보기를 닫는다.
- 삭제 성공 후 목록을 즉시 갱신하고 토스트로 결과를 알린다.

## 확인된 원인

- `agents/dashboard/static/js/views/reports.js`에 삭제 UI와 삭제 요청 로직이 없다.
- `agents/dashboard/serve.py`에 리포트 삭제 API가 없다.
- 현재 리포트 행은 바깥 `button` 안에 `새 탭` 버튼이 중첩된 구조라 상호작용 마크업이 올바르지 않다.

## 구현 대상

- `agents/dashboard/static/js/state.js`: 검색·정렬·선택 상태 추가.
- `agents/dashboard/static/js/views/reports.js`: 체크박스, 전체 선택, 개별/선택 삭제, 분할 미리보기, 새로고침 구현 및 중첩 버튼 제거.
- `agents/dashboard/static/css/views/reports.css`: 승인 시안의 레이아웃·상태·반응형 스타일 적용.
- `agents/dashboard/serve.py`: 안전한 HTML 리포트 삭제 API 추가. 파일명 경로 탈출, 비 HTML 파일, 빈 목록을 거부한다.
- `doc/API_REFERENCE.md`: 삭제 API 계약 추가.
- 테스트: 삭제 API 보안·성공·누락 파일 검증 및 실제 브라우저에서 체크박스 선택→확인 모달→삭제→목록/미리보기 갱신 E2E.

## 재개 지시

새 세션에서 `doc/REPORT_MANAGEMENT_HANDOFF.md를 읽고 승인된 리포트 관리 UI 작업을 구현부터 검증까지 이어서 진행해줘`라고 요청하면 된다.
