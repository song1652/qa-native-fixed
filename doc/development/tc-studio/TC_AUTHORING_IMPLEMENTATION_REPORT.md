# TC Authoring Studio 구현 보고

개발 당시 작업 위치: 별도 worktree(`qa-native-tc-studio`)의 `feat/tc-studio-phase1` 브랜치.
2026-10-01 main에 fast-forward 병합했고 worktree는 정리했다. 이후 작업은 저장소 루트의 main에서 한다. 아래 Phase 보고의 경로·브랜치 표기는 당시 기록이다.

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

### 빈 기본 양식·구조 추가·디자인 모달 (사용자 후속 요청)

- 기본 양식에서 원본 서비스별 시트 이름이 남은 것을 확인했다. 기존 기본양식의 삭제 이력은 state/template_backups/기본양식-20260930-171656에 보관하고, 기본양식을 테스트케이스 시트 하나·빈 분류·TC 0건으로 다시 가져왔다. ~/Downloads/TC_빈양식.xlsx도 같은 중립 양식으로 갱신했다. 기존 활성 TC가 있으면 대체하지 않도록 확인 도구에서 검사했다.
- 시트 추가: 기존 엑셀의 컬럼·서식·드롭다운만 복사한다. TC 내용은 복사하지 않는다. 새 빈 데이터 행 스타일 누락을 추가 RED로 확인하고 보존하도록 수정했다.
- 분류 추가: 대·중·소분류 입력 후 분류 추가를 누르면 TC 생성 전에도 저장된다. branches 메타데이터에 저장하며 트리에 TC 0건 가지로 표시한다. 중복 추가는 멱등, 누락된 상위 분류·잘못된 시트는 거부한다. 시트 이름 변경 시 빈 분류의 시트 이름도 갱신한다.
- 시트 추가·이름 변경 모달: 브라우저 기본 prompt 제거. 기존 scrim/modal 스타일, 제목·입력·저장/추가·취소 버튼·오류 안내 적용. 중복 이름 오류 후 재입력, 취소·ESC, 포커스 복원 검증.
- API: POST /api/tc-library/{suite}/sheets {name}; POST /api/tc-library/{suite}/branches {sheet, path}; 기존 /sheets/rename 사용.
- 사용자 흐름: 기획 정보 · TC 생성 → 오른쪽 시트 추가 → 이름 입력·추가 → 대분류 입력(중·소분류 선택) → 분류 추가 → 왼쪽 PRD/텍스트/URL 입력 → 초안 생성.
- 검증: tc_library 121 passed; 전체 798 passed, 1 skipped, 기존 경고 2개. 실제 서버 화면에서 별도 확인용 스위트로 빈 시트 추가→디자인 모달 이름 변경→대·중·소분류 추가→새로고침 유지·TC 0건·JS 오류 없음 확인. 확인용 스위트는 state/template_backups에 보관해 기본 화면에는 남기지 않았다. API 스위트 목록은 기본양식·테스트케이스 시트·0건만 존재.
- 증거: /tmp/tc-structure-unit.log, /tmp/tc-structure-full-final.log, /tmp/tc-structure-live.log, /tmp/tc-studio-rename-sheet-modal-final.png, /tmp/tc-studio-neutral-structure-final.png.
- 계획과 다르게 한 것: 사용자 후속 요청에 따라 빈 분류 메타데이터·시트 추가 API·디자인 모달 추가 및 로컬 기본 양식의 서비스별 이름 제거. Push·병합 없음.

### 기본 작성 프로필 정리 (사용자 후속 요청)

- 확인: 기존 기본 규칙에 정상·예외·유효성 최소 개수, 코호트·D+날짜 예시, 자동화 가능 여부 추정이 포함되어 있었고 생성 역할은 모바일 앱 QA로 고정되어 있었다.
- 변경: 기본 공통 규칙 4개(제공한 정보만 사용, TC 하나에 한 검증 목적·중복 제거, 결과가 다르다고 명시된 조건만 분리, Step/Expected 문체). 기본 최소 개수는 모두 0. 역할은 QA 엔지니어. 문서 또는 사용자 작성 규칙에 우선순위 정보가 없으면 P2, 자동화 정보가 없으면 AUTO 빈 값. 작성 패널 이름은 작성 규칙, 예시가 없는 경우 입력한 정보와 규칙으로 생성한다고 안내한다. PRD F3 기본값도 갱신했다.
- 테스트: 기본 프로필의 강제 부족분 없음·공통 프롬프트·빈 예시 안내 RED 확인 후 GREEN. 기존 저장소/API 커버리지 assertion은 엄격 프로필을 명시하는 준비 단계로 변경하고 원래 정상 케이스 부족 assertion을 유지했다. 기본 프로필의 부족분 없음 API assertion도 추가했다. tc_library 122 passed; 전체 799 passed, 1 skipped, 기존 경고 2개.
- 실제 LLM: 별도 확인용 빈 스위트에 주신 엑셀의 혜택 탭 버튼 설명을 입력하여 기본 모델로 TC 1건 생성. P2·AUTO 빈 값·quote_found true 확인, JS 오류 없음. 확인용 스위트는 state/template_backups에 보관하여 기본 화면은 테스트케이스 시트 하나·TC 0건 유지.
- 증거: /tmp/tc-profile-unit-final.log, /tmp/tc-profile-full-final.log, /tmp/tc-profile-live.log, /tmp/tc-profile-generated-cases.json, /tmp/tc-studio-common-writing-rules.png, /tmp/tc-studio-common-rules-generated.png.
- 계획과 다르게 한 것: 사용자 후속 요청에 따라 PRD F3와 검증된 계획의 기본 프로필 정책을 공통·문서 근거 중심으로 변경했다. 기존 커버리지 기능은 명시적인 엄격 프로필 테스트로 검증을 유지했다. Push·병합 없음.

## 실제 사용자 흐름 검증 보고 (2026-09-30)

- 끝낸 작업: 화면이 보이는 Chromium에서 기획 정보 입력 → 실제 로컬 LLM 생성·재생성 → TC 수정·승인 → Excel 왕복 → md 미리보기·반영·롤백 → 단일 파이프라인 버튼 실행 → 생성된 실제 Playwright 테스트 실행 → 웹 HTML 리포트 확인. 후속 수정과 검증 결과 커밋 5개, 브랜치 feat/tc-studio-phase1. Push·병합 없음.
- 테스트: tests/unit/tc_library **126 passed** / 전체 **803 passed, 1 skipped**, 기존 경고 2개. 실제 파이프라인 **5 passed, 0 failed, 0 skipped**, 힐링 0회. 같은 테스트의 브라우저 표시 빠른 실행도 5/5 통과. 마지막 제목·분류 수정 후 단일 파이프라인 재실행도 5/5 통과. Skip은 기존 P63의 TEST_DATA_PATH 참조 검사이며 해당 구형 데이터 경로 참조가 없어 스킵된다. 실제 생성 테스트 5개는 스킵되지 않았다.
- 수동 확인: 사용자 문서가 없어 회원 등록 로컬 페이지와 PRD.md를 작성했다. 페이지에서 이름 미입력·이메일 형식 오류·약관 미동의·정상 등록·초기화의 다섯 동작과 화면 문구를 직접 조작해 확인했다. TC 데이터나 파이프라인 상태를 API로 주입하지 않고 화면의 파일 선택·입력·버튼으로 작업했다. 실제 로컬 LLM 신규 생성 3회(5건·1건·1건), 메모 재생성 1회, 코드 생성 단일 파이프라인 2회 확인. 화면 입력과 산출물은 삭제하지 않고 남겨 두었다.
- 계획과 다르게 한 것: 사용자 후속 요청에 따라 실제 사용 검증에서 발견한 ① 자동 실행 권한 제한 ② feature 제목·시트/분류 구분 지시 ③ 기존 스위트의 필터 해제·서버 저장 생성 작업 복원 ④ 자동 실행 자식 CLI의 훅 분리를 추가했다. 기존 훅이 다른 세션의 서버 재시작 지시를 자동 실행에 주입했으므로 자식 CLI에만 disableAllHooks를 적용했다. 수동 Claude 훅 설정은 변경하지 않았다. 각 수정은 실패 테스트 확인 → 구현 → 통과 → 커밋. 기존 계획 assertion을 약하게 변경하지 않았다. 새 API와 복원 동작은 PRD F1.7/D7에 기록했다.
- 발견한 문제·위험: 위 네 가지는 agents/lessons_learned.md에 기록하고 수정했다. 실행 스크립트가 지운 기존 추적 스크린샷·영상은 복원했다. 회사 Confluence/Figma 인증 정보가 없어 연결 설정 UI와 기존 녹화 응답 테스트까지 확인했으며 실제 회사 문서 수집은 확인하지 않았다. 사용자가 단일 또는 병렬을 허용해 단일 코드 생성 파이프라인을 선택했다. Studio의 Pass 값은 실제 5/5 통과 결과를 확인한 뒤 화면의 일괄 수정으로 기록했다. 파이프라인에서 Studio로 자동 동기화한 결과는 아니다.
- 사람이 결정해야 할 것: 없음. 기존 브라우저 탭은 새로고침하면 수정된 스위트 복원 동작을 사용할 수 있다.

### 지금 웹에서 볼 수 있는 정보

| 위치 | 남겨 둔 내용 |
|---|---|
| http://localhost:8766/tc-studio | TC스튜디오_실사용: 서로 다른 제목 5개, 회원등록 › 등록 폼, 승인·P1·Pass |
| 기획 정보 · TC 생성 | 저장된 PRD.md + 직접 입력한 설명, 대상 시트·분류, 완료 작업, 초안 검토·재생성 버튼 |
| TC스튜디오_편집검증 | 실제 생성·메모 재생성·원문 확인·반려/되돌리기·일괄 승인·복제/삭제/복원·이력 되돌리기·수동 작성·일괄 수정·검색/필터·계층 이동을 확인한 데이터 3건 |
| TC스튜디오_엑셀왕복 | 최신 Excel을 다시 가져온 TC 5개. 제목·분류·Step·Expected·우선순위·Pass 유지 |
| TC스튜디오_생성개선확인 | 수정한 생성 지시로 실제 LLM이 만든 목적별 제목 1개, 중복 없는 분류, 승인 |
| 기본양식 | 테스트케이스 시트 하나·분류 없음·TC 0건 유지. 야핏무브 데모 없음 |
| 단일 파이프라인 | Total 5, Passed 5, Failed 0, Pass Rate 100%, 최신 리포트 보기 |
| http://localhost:8766/reports/report_20260930_183846.html | 제목·분류 수정 후 최신 5/5 통과 HTML 리포트 |
| http://localhost:8877 | 실제 테스트한 회원 등록 페이지. 서버 유지 |

### 검증한 화면 작업

| 작업 | 결과 |
|---|---|
| 빈 Excel 가져오기·시트 추가·디자인 모달 이름 변경·빈 분류 추가 | 성공 |
| 파일 PRD + 붙여넣기 정보 입력 → 실제 로컬 claude 생성 | 5 TC 생성 |
| 공개 HTTPS URL 수집·소스 제거·연결 설정 | example.com 수집 성공. 미연결 Confluence/Figma 설정 화면 확인 |
| 작성 규칙 편집·이름 저장 → 생성·메모 재생성 | 실제 LLM으로 성공 |
| TC 원문·변경 이력·수정·문구 확인·승인·반려·되돌리기 | 성공 |
| 복제·삭제·삭제 복원·수동 추가·일괄 수정·검색·필터·분류 이동 | 성공 |
| Excel 검사·다운로드·다시 가져오기 | 2시트 × 왕복 일치/수식 참조 = 4개 OK, TC 5개 유지. 기존 6시트 검증의 12개와 같은 검사 기준 |
| md 그룹 매핑·미리보기·반영·롤백·재반영 | 5파일 성공, 제목 변경 반영 후에도 ID TSD_01~05 유지 |
| 페이지 URL 관리 → 단일 파이프라인 실행 버튼 | 실제 로컬 claude가 자체 완결 테스트 파일·영문 함수 5개 생성. TODO/pass scaffold 없음 |
| 실행 결과·리포트 열기·리포트 목록 미리보기 | 5/5 통과 확인 |
| 기존 스위트 전환·검색 필터 해제·새로고침·새 브라우저 | 기존 TC·소스·대상·검토 작업 복원, 새 Excel 요청 없음 |

### 산출물·증거

- 재현용 페이지·기획 정보: tests/fixtures/tc_studio_demo/index.html, PRD.md, README.md.
- 실제 Studio에서 반영한 md 5개: testcases/tc_studio_demo/.
- 실제 파이프라인이 작성한 테스트 5개: tests/generated/tc_studio_demo/.
- 최신 단일 리포트: tests/reports/report_20260930_183846.html. 브라우저 표시 빠른 실행 리포트: tests/reports/parallel_index_20260930_181408.html. 이전 실행 리포트도 보존했다.
- 화면 추적·스크린샷·입력/작업 기록·다운로드 Excel: state/tc_studio_user_flow/. state는 gitignore 대상이나 현재 PC와 웹에 보존한다.
- 주요 증거: actions.log, final.json, TC스튜디오_실사용.xlsx, authoring-trace.zip, export-pipeline-trace.zip, editing-trace.zip, results-trace.zip, repair-trace.zip, delivery-trace.zip, 18-final-saved-sources.png, 20-final-clear-titles.png, 21-final-priority-and-pass.png, 22-latest-pipeline-report.png, 23-report-list-preview.png.
- RED/GREEN 로그: /tmp/tc-human-launch-red.log·green.log, /tmp/tc-human-title-red.log·green.log, /tmp/tc-human-suite-red.log·green.log, /tmp/tc-human-context-red.log, /tmp/tc-human-hook-red.log·green.log. 실제 훅 분리 CLI: /tmp/tc-human-hook-live.log (QA_HOOK_ISOLATION_OK).
- 최종 검사 로그: /tmp/tc-human-library-final.log, /tmp/tc-human-full-final-committed.log. 실제 파이프라인은 logs/run_qa_headless.txt, 브라우저 표시 빠른 실행은 logs/quick_run.txt.

### 제목 항목 표시 (사용자 후속 요청)

- 대·중·소분류 옆 그리드 컬럼을 기능 → 제목으로 변경. 트리 경로 안내·검색 입력·상세 입력의 접근성 이름·계층 이동 모달·새 TC의 초기 제목도 일치시켰다.
- 헤더 계약 assertion RED 확인 후 관련 실제 브라우저 테스트 3 passed. 실제 서버의 화면 표시 Chromium에서도 제목 컬럼과 제목 상세 입력·기존 TC 5건 유지 확인. 증거: state/tc_studio_user_flow/24-title-column.png, /tmp/tc-title-label-live.log. Push 없음.

## Import 기능의 TC 스튜디오 통합 (2026-09-30)

사용자 승인에 따라 [통합 계획](plans/2026-09-30-import-integration.md)의 기능을 추가했습니다. 기존 Import 전용 메뉴·JS/CSS를 제거하고 `/import-studio`에서 `/tc-studio`로 이동합니다. 공용 md 엔진과 `/api/import/*`, 기존 매핑·작업·스냅샷 자료는 유지합니다.

- Excel 가져오기: 파일당 25MB 상한으로 여러 파일 선택, 공통/시트별 매핑, 기존 프로필 읽기와 새 프로필 저장·수정·삭제.
- 원본 보존: 내부 case_id와 source_tc_id 구분, 원본 태그·대중소분류 보존.
- 변경 확인: 화면에서 변경 미리보기 후 반영. 신규·갱신·동일·충돌·오류와 before/after 표시, 충돌 skip/overwrite·오류 skip 결정. 반영 직전 업로드와 스위트 변경 검사.
- 작업·복구: Excel→라이브러리 작업 목록·상세와 템플릿 포함 복구, 이후 편집 시 복구 거부. 기존 Excel→md 및 TC→md 이력·제외 CSV·복구. TC md 작업은 내보내기 기록도 복구.
- 검증 오류: 매핑·JSON 입력 오류는 400, 본문 크기 초과는 413. 손상된 작업은 오류 안내를 표시하고 다른 작업 조회를 계속 제공.
- 제한: 여러 파일의 동일 이름 시트는 한 작업에 선택할 수 없음(`DUPLICATE_SHEET`). 다른 양식은 먼저 공통 매핑으로 파일 분석을 통과한 뒤 시트별 프로필을 적용.

문서: [사용자 설명서](../../guides/tc-studio/TC_AUTHORING_USER_GUIDE.md) 가져오기·이력 절차, [API](../../reference/API_REFERENCE.md) 통합 계약, [통합 검토](IMPORT_STUDIO_INTEGRATION_REVIEW.md) 최종 설계와 제한을 반영했습니다.

최종 통합 검증: 아래 자동화 여부 제거 후속 검증까지 포함하여 전체 **856 passed, 1 skipped**, `tests/unit/tc_library` **178 passed**. 별도 Import 공용 엔진·대시보드·core 회귀가 전체 명령에 포함됩니다.

## 자동화 여부 제거 후속 변경 (2026-09-30)

사용자 명시 요청으로 AUTO 필드와 관련 매핑·생성 규칙·입력·필터·일괄 수정·md 대상 분기·Excel 열을 제거했습니다. 현재 md 조건은 승인·검증 오류 없음·추정 문구 없음·URL 그룹 매핑입니다. 위 Phase와 과거 LLM 검증에 등장하는 AUTO/Y-web 값은 당시 검증 기록이며 현재 동작을 의미하지 않습니다. 초기 Phase 계획 원문은 보존합니다. 배포 샘플 빈 양식의 해당 열·요약과 드롭다운도 제거하고 TC 0건을 유지합니다. 후속 전체 회귀와 실제 가져오기 재검증을 완료했습니다.

### 최종 확인과 작업 인계

- 테스트: `.venv/bin/python -m pytest tests/unit -q` → **856 passed, 1 skipped** (150.01초). `.venv/bin/python -m pytest tests/unit/tc_library -q` → **178 passed** (112.50초).
- TDD: ID/태그 왕복, 프로필 CRUD, 작업 반영·복구·동시 writer, UI 초기화/미리보기 경쟁, AUTO 제거, AUTO 요약과 전체 열 수식 이동 각각 실패를 확인한 후 수정했습니다. 기존 검증을 삭제하지 않았고, AUTO 대상 제한이 사라진 테스트는 더 많은 승인 TC의 정확한 수·ID·내용을 확인하도록 갱신했습니다.
- 실제 화면: Chromium을 표시한 상태에서 2개 Excel과 시트별 다른 프로필을 가져오고, 원본 ID·태그 표시·태그 수정·다시 열기, 충돌 skip/overwrite, 라이브러리 rollback, 편집 후 rollback 거절, md 반영/rollback/재반영, 새 빈 양식 0건을 확인했습니다. 기존 History 시트와 원본 파일도 보존했습니다.
- 실제 LLM: 로컬 Claude로 이메일 형식 검증 초안 1건을 생성했습니다(`job_b5ed1e084acd`, done, kept=1, invalid=0, cost_usd=0.0479). 실제 localhost:8877에서 오류 문구를 확인하고, 화면에서 문구를 확인 상태로 변경·저장·승인했습니다. 기존 2건과 함께 Excel/md 최종 3건을 내보냈습니다. 테스트 코드 실행은 이번 범위에 포함하지 않습니다.
- 웹 자료: `TC스튜디오_가져오기통합` 승인 TC 3건, `TC스튜디오_빈양식확인` TC 0건, 매핑 프로필과 작업 이력을 남겼습니다. 기존 스위트·파이프라인 상태는 보존했습니다.
- 증거: `state/tc_studio_import_integration/result.json`, `trace.zip`, 화면 `01`~`13`, `생성포함_최종.xlsx`; 내보낸 md는 `testcases/tc_studio_demo/`에 있습니다. 실패 단계의 화면은 별도 `state/tc_studio_import_integration/red-screenshots/`에 보관합니다.
- 문서: 사용자 안내서의 최신 실제 화면 6개, 통합 절차, PRD·요소 명세·API·로드맵·빈 양식·기획 예시를 갱신했습니다.
- 계획과 다르게 한 것: 사용자 후속 요청에 따라 AUTO를 전부 제거했습니다. 기존 Phase 계획은 과거 기록으로 유지합니다. 운영 데이터/API 호환을 위해 공용 Import 엔진과 기존 저장 AUTO 값은 수정하지 않으며, 현재 TC 화면·응답·작성·내보내기에 영향을 주지 않습니다.
- 제한: 한 가져오기 작업에서 여러 파일의 동명 시트는 함께 선택할 수 없습니다. 시트 이름을 구분하거나 파일별로 가져오세요. Windows 잠금 분기는 구현했지만 이 Mac 환경에서는 실행 검증하지 못했습니다.
- 당시 작업 위치: worktree `qa-native-tc-studio`, `feat/tc-studio-phase1`. 이후 main에 병합했습니다(아래 “사용자 피드백 후속 수정”). 실사용 생성 자료(`state/tc_library` 등)는 저장소 루트의 `state/`로 옮겼습니다.

## 사용자 피드백 후속 수정 (2026-09-30 ~ 10-01)

실사용 중 받은 피드백을 고쳤다. 사용법은 사용자 설명서, 계약은 PRD·요소 명세·API 레퍼런스에 반영했다.

| 영역 | 변경 | 커밋 |
|---|---|---|
| 스위트 휴지통 | 삭제한 스위트 영구삭제(행 안 2단계 확인, 서버 스위트 이름 확인, 복원과 같은 잠금) | f329a35 |
| 엑셀 가져오기 | 영문 헤더(Main Category·TC Summary·Step) 인식, 시트 0개 안내, Test Level→우선순위, 수식 원본 ID는 계산 결과 | f329a35 |
| 기본양식 | 삭제 금지(서버·메뉴), 가져오기 스위트 이름 기본값은 파일 이름 | 825a31a |
| 가져오기 500 | 다른 워크북의 셀 서식을 번호가 아닌 값으로 복사 | 825a31a |
| 성능 | 미리보기에서 워크북을 한 번만 연다(LODIS 1,731건 29초→약 4.5초), 성능 테스트 `test_tc_import_perf.py` | 825a31a |
| 화면 | 파일 분석 중 표시, 첫 화면 깜빡임·재진입 시 잘못된 탭, 가져오기 다음 단계 버튼 강조, 내보내기 시트 체크박스 | 825a31a·c8454e0·7a755d1·4e7be42·0bc5db5 |
| 톤앤매너 | 프로필 기준 예시·Expected 끝맺음·금지 표현 검사(초안 ‘문체 확인’ 경고), 엑셀에서 문체 가져오기 API·버튼 | e6401a0 |
| 파일 이름 | macOS 한글 파일 이름(NFD)에서 스위트 이름이 `_`로 깨지던 문제 | 62f3c06 |
| 가져옴 구분 | `review_source`: 엑셀에서 가져온 케이스는 ‘가져옴’, 검토 상태 잠금, 승인 필터·승인 내보내기에서 제외, 도입 전 데이터는 변경 이력으로 1회 보정 | 72561b2 |

- 가져옴 판별 방식은 에이전트 3명(데이터 판별·UX·위험 검토) 논의로 정했다. `import_origin`은 재가져오기 때 덮여 사람이 승인한 케이스까지 잠글 수 있어 별도 필드를 두었다. 표시가 없으면 추측하지 않는다.
- 로컬 데이터 결과: LODIS 1,731건·가져오기통합 2건·엑셀왕복 5건이 가져옴, 실사용 5건(생성 후 사람 승인)은 승인 유지.
- 로컬 작성 프로필 ‘톤앤매너’: 야핏무브_Full.xlsx 911건에서 추출(규칙 4, 끝맺음 `된다.`·`는다.`·`한다.`, 기준 예시 5건). 실제 LLM으로 말투 일치를 확인하는 작업은 남았다.
- 병합: main에 커밋되지 않았던 문서 재구성은 브랜치의 재구성이 대체하므로 `git stash`(“TC 스튜디오 병합 전 main 미커밋 문서 재구성”)로 보관하고 fast-forward 병합했다.

