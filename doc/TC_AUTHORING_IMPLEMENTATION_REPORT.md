# TC Authoring Studio 구현 보고

작업 위치: `/Users/junghoyoung/qa-native-tc-studio` (기존 작업 폴더 변경을 보존한 별도 worktree).
브랜치: `feat/tc-studio-phase1`. 모든 Phase를 같은 브랜치에 순서대로 누적한다. Push하지 않는다.

## Phase 1 보고
- 끝낸 작업: B1~B10, W1~W4 (작업별 14개 커밋).
- 테스트: tests/unit/tc_library 40 passed / 전체 717 passed, 1 skipped. 기존 pytest 경고 2개.
- 수동 확인: Chromium 대시보드에서 실제 야핏무브_Full.xlsx 6시트·926건 가져오기, BEN_0001 우선순위 P3 수정, 내보내기 무결성 12개 OK, 내려받기, 재가져오기 추가 0·갱신 0·그대로 926. 원본 SHA-256 유지, JS 오류 없음. 출력의 P0~P3 드롭다운과 History 마지막 입력 행 확인. Excel 앱에서 수식 숫자 재계산·표시 확인은 미수행.
- 계획과 다르게 한 것: B6의 미사용 verify_export import를 함수가 정의되는 B7로 이동. W2의 빈 테스트 블록을 실제 가져오기 E2E로 보완. 실제 파일 확인에서 발견한 공통 5초 폴링/SSE 재렌더를 피하도록 static/js/api.js의 _shouldSkipRender에 tc_studio 추가하고 DOM 유지 검사로 RED→GREEN 확인. 명세서의 케이스 경로는 W4 기대값 0을 충족하도록 8장 외 표에도 동일하게 반영. 이 보고 파일을 진행 증거로 추가.
- 발견한 문제·위험: 위 3가지 구현 문제는 agents/lessons_learned.md에 기록. 실제 엑셀에서 기존 검증 오류 15건은 가져온 원문을 보존한다.
- 사람이 결정해야 할 것: 없음. 사용자 지시에 따라 다음 Phase로 이어간다.
