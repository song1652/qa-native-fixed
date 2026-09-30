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

## Phase 4 보고

- 끝낸 작업: M1~M3, W12~W13 (작업별 5개 커밋, 브랜치 feat/tc-studio-phase1).
- 테스트: tests/unit/tc_library 113 passed / 전체 790 passed, 1 skipped (3회 연속: 94.15s, 93.67s, 93.71s). 기존 경고 2개. M1 지정 Import Studio·대시보드·core 회귀에 경로 복원 검증을 포함해 266 passed, 1 skipped.
- 수동 확인: coverage_matrix.py → state/coverage.json 생성, sync_test_data.py --dry-run → 누락 없음. 별도 임시 프로젝트와 실제 로컬 초대 웹 페이지에 pages.json 그룹을 만들고, 한국어 화면 문구를 확인한 승인·Y-web 케이스 1건을 스튜디오 화면으로 매핑→미리보기→md 반영했다. 실제 claude가 기존 DOM 분석·전략·scaffold·직접 코드 작성·lint·리뷰·승인·실행·리포트 파이프라인을 완료했고 1 passed, 0 failed, 100%, heal_count 0, step done. md 직접 수정 후 FILE_DRIFT 확인. md의 very_high·source_ref·data_key null 및 생성 코드의 한국어 assertion을 확인했다. 회사 실서비스 URL 대신 격리된 로컬 페이지로 파이프라인 연결을 검증한 범위다.
- 계획과 다르게 한 것: M1 지정 회귀 순서에서 기존 dashboard_server가 임시 경로를 복원하지 않아 core 테스트 27개 오류가 발생했다. 기존 Studio fixture에 종료 후 경로 동일 assertion을 추가해 RED를 확인하고 서버 context 종료 시 _paths·serve 경로 및 Host/Origin을 복원해 GREEN을 확인했다. 실제 파이프라인은 금지된 권한 플래그를 쓰는 기존 자동 실행기를 호출하지 않도록 run_qa.py --no-auto 후 acceptEdits 및 명시적으로 허용한 파일·Python 도구로 claude를 실행했다. 별도 worktree·임시 프로젝트의 초기화와 macOS /var 경로 정규화는 수동 검증 도구에만 적용했다. 최종 문서 검토에서 API 표 복사 중 누락된 개행도 수정했다.
- 발견한 문제·위험: 테스트 경로 누수는 lessons_learned.md에 기록하고 수정했다. 회사 웹 서비스의 실제 TC는 별도 검증이 필요하며, 이번 100%는 로컬 웹 smoke 1건의 결과다.
- 사람이 결정해야 할 것: 없음. Push·병합은 수행하지 않았다.

## 검증 자료
- Phase 1 전체: /tmp/tc-w4-full.log; tc_library: /tmp/tc-w3-green.log; 실제 926건 왕복: /tmp/tc-phase1-manual.log.
- Phase 2 전체: /tmp/tc-w8-full.log; tc_library: /tmp/tc-phase2-unit.log; 실제 생성·승인·엑셀: /tmp/tc-phase2-manual.log; 화면: /tmp/tc-phase2-real-review.png.
- Phase 3 전체: /tmp/tc-phase3-full-green.log; tc_library 반복: /tmp/tc-phase3-repeat-{1,2,3}.log; 상세 경쟁 조건 재현·검증: /tmp/tc-w10-race-red.log, /tmp/tc-detail-race-green-{1..5}.log.
- Phase 4 전체 반복: /tmp/tc-phase4-full-{1,2,3}.log; tc_library: /tmp/tc-phase4-unit.log; 지정 회귀: /tmp/tc-m1-regression-green.log; 실제 파이프라인: /tmp/tc-phase4-manual.log; 화면: /tmp/tc-phase4-md.png.
- 실제 파이프라인 산출물: /private/var/folders/q4/qsd5zshs6mnd052zbpjftxsh0000gn/T/tc-phase4-pipeline-qn3li4x_/ (md, 생성 Python, 상태, claude-pipeline.log, tests/reports/report_20260930_100933.html). 임시 자료는 저장소에 커밋하지 않았다.

## 사용자 후속 확인·수정 (2026-09-30)

- 실제 실행 서버: 구현 worktree에서 http://localhost:8766/tc-studio. 같은 서버의 /api/tc-library API에 연결.
- 우선순위 바로 다음에 실행 결과 컬럼을 배치. 기존 E2E에 헤더·셀 위치 검증을 추가하여 RED 확인 후 8 passed, 전체 790 passed, 1 skipped.
- 기본 샘플은 본문이 없는 양식이라는 사용자 요구를 반영. 빈 양식의 시트가 생성 화면에서 사라지는 문제를 발견하고, 저장된 스위트 시트 목록을 함께 사용하도록 수정. 빈 엑셀 가져오기·0건·6시트·대상 분류·소스 입력 흐름 확인. E2E 9 passed, 전체 791 passed, 1 skipped (기존 경고 2개).
- 실제 로컬 LLM: 빈 양식에 사용자 제공 엑셀의 혜택 탭 버튼 설명을 발췌해 TC 1건 생성. 화면에서 기능명을 수정하고 새로고침 후 저장 유지 확인. 확인용 TC는 UI에서 삭제해 기본양식 0건 유지. 생성 산출물은 /tmp/tc-blank-generated-cases.json, 화면은 /tmp/tc-studio-blank-generated-edit.png. 빈 양식 파일은 ~/Downloads/TC_빈양식.xlsx.
- 야핏무브 확인용 스위트 및 보관본은 사용자 삭제 요청으로 제거. API에는 기본양식 6시트·0건만 존재.
- 계획과 다르게 한 것: 사용자 후속 요청에 따른 컬럼 위치 변경 및 빈 양식 생성 흐름 보완. 새 분류에 기존 예시 TC를 채워 넣지 않고 작성 규칙·입력 문서로 생성한다. Push·병합 없음.

### 작성 시작 화면·시트 이름 후속 수정

- 사용자 요청: 온보딩 자동 선택 이유 확인, 시트 이름 변경, 첫 화면의 PRD·URL 입력 위치 개선.
- 변경: 초기 시트는 “시트를 선택하세요”. 첫 탭은 “기획 정보 · TC 생성”. 빈 스위트로 접속하면 “1. 기획 정보 입력” 화면이 열린다. PRD 파일·텍스트·PRD URL·Confluence·Figma 입력 탭을 안내한다. 시트를 선택하면 “이름 변경” 버튼으로 수정 가능. 빈 분류는 이름 입력칸을 바로 표시한다.
- 이름 변경 API: POST /api/tc-library/{suite}/sheets/rename, JSON {sheet, name}. TC ID·내용 보존, 변경 이력·rev 갱신, 엑셀 시트·프로필·기존 생성 작업 대상·md 그룹 경로 동기화. 잘못된 이름·중복 이름·실행 중 생성 거부. 저장 실패 시 기존 파일 복구. 영문 대소문자만 변경해도 숫자 접미어가 붙지 않도록 처리.
- 검증: 자동 선택·이름 변경·첫 정보 입력 화면·빈 분류 입력의 RED 확인 후 GREEN. tc_library 118 passed; 전체 795 passed, 1 skipped, 기존 경고 2개. 실제 실행 서버의 온보딩 시트를 테스트케이스로 변경하고 새로고침 유지 확인. PRD 파일 영역과 URL 입력칸 노출 확인, JS 오류 없음. 기본양식 0건 유지.
- 계획과 다른 점: 사용자 후속 요청에 따라 첫 탭·초기 진입 화면과 시트 관리 기능 추가. 기존 생성 E2E는 대상 시트를 명시적으로 선택하도록 준비 단계만 수정하고 기존 생성·검토 assertions 유지. 새 이력 검사의 시간 순서는 저장소가 최신순을 반환하는 계약에 맞춰 확인했다.
- 증거: /tmp/tc-authoring-followup-unit-final.log, /tmp/tc-authoring-followup-full-final.log, /tmp/tc-studio-prd-entry.png, /tmp/tc-studio-url-entry.png, /tmp/tc-studio-sheet-rename.png. Push·병합 없음.
