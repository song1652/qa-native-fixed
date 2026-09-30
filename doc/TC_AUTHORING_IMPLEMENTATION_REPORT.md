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

## Phase 2 보고
- 끝낸 작업: G1~G7, W5~W8 (작업별 11개 커밋, 브랜치 feat/tc-studio-phase1).
- 테스트: tests/unit/tc_library 77 passed / 전체 754 passed, 1 skipped. 기존 경고 2개.
- 수동 확인: 실제 로컬 claude 2회. G5 haiku에서 배너 초안 3건·인용 확인. W8 Chromium에서 실제 TC_AUTHORING_PRD.md F1/F2 원문 발췌를 기본 모델에 전달하여 초안 31건·형식 오류 0건, 인용 31/31 일치, 원문 하이라이트·한국어 유지·추정 배지 9건 확인. 2건 승인 후 라이브러리와 다운로드한 xlsx의 ID 확인, JS 오류 없음. 배너 개편 실제 기획서는 로컬에 없어 실제 보유 PRD의 TC 스튜디오 가지로 확인했다.
- 계획과 다르게 한 것: W5의 W6 선행 의존 assertion(검토 배지·카드·탭)을 W6로 이동하여 보존했다. W6 빈 테스트 블록을 승인·반려·되돌리기·원문·재생성 E2E 2개로 보완했다. 재생성 후 job_id가 바뀌어 검토 목록에서 사라지는 결함은 원래 job_id 유지·regenerated_job_id 추가로 수정했고 동일 E2E가 RED→GREEN 통과했다. W8의 경로 0건 조건을 충족하도록 8장 외 표에도 API 경로를 반영했다.
- 발견한 문제·위험: W5/W6 계획 누락과 재생성 결함을 lessons_learned.md에 기록. 실제 서비스별 기획 문구 검토는 사용자 문서로 추가 확인 가능하다.
- 사람이 결정해야 할 것: 없음. 사용자 지시에 따라 Phase 3으로 이어간다.

## Phase 3 보고
- 끝낸 작업: C1~C5, W9~W11 구현·문서 (작업별 8개 커밋, 브랜치 feat/tc-studio-phase1). 실제 회사 계정 확인은 미수행.
- 테스트: tests/unit/tc_library 99 passed (3회 연속) / 전체 776 passed, 1 skipped. 상세 저장 경쟁 조건의 단독 재현 검사 수정 후 5회 연속 통과.
- 수동 확인: 실제 공개 HTTPS https://example.com 수집 → 제목 Example Domain, markdown 185자·버전 해시 12자 확인. Confluence·Figma·버전 변경·이미지는 녹화 응답과 Chromium E2E로 확인했다. 원본/작업 worktree의 자격증명 파일과 환경변수 모두 없음을 값 노출 없이 확인하여 회사 실계정 수집은 수행하지 않았다.
- 계획과 다르게 한 것: W10에서 배너 조회로 드러난 상세 저장 경쟁 조건을 수정했다. 기존 저장·이력·되돌리기 테스트에 배너 지연·저장 완료 검증을 추가하고 saveDetail의 두 번째 open에 현재 탭을 전달했다. W11은 실제 계정 자격증명이 없어 로드맵에 구현·자동 테스트 완료와 실계정 미확인을 분리해 기록했다. 사용자 연속 진행 지시에 따라 이를 기록하고 Phase 4로 진행한다.
- 발견한 문제·위험: 상세 탭 경쟁 조건은 lessons_learned.md에 기록하고 수정. 실제 Confluence·Figma 응답·권한·이미지와 회사 문서의 복잡한 매크로는 추가 확인이 필요하다.
- 사람이 결정해야 할 것: 회사 계정으로 연결 및 실제 문서 확인을 나중에 수행해야 한다. 구현 진행을 위한 질문은 하지 않는다.
