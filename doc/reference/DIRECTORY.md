# 디렉토리 구조

> **자동 생성** — `python scripts/update_directory.py` | 마지막 갱신: 2026-10-01 02:29
> 최근 실행: 2026-09-29 13:18 | quick | api_demo | 0/1 | heal:0

> 역할 설명 수정: `scripts/update_directory.py` 내 `SCRIPT_DESCRIPTIONS` / `FOLDER_DESCRIPTIONS` 편집.

---

## 루트

| 파일 | 역할 |
|------|------|
| `_bootstrap.py` | 프로젝트 진입점 공통 경로 설정 (루트 스크립트가 import) |
| `run_qa.py` | 단일 파이프라인 실행 엔트리포인트 |
| `run_qa_parallel.py` | 병렬 파이프라인 실행 엔트리포인트 |
| `run_team.py` | 팀 토론 실행 엔트리포인트 |

## scripts/ — 단계별 실행 스크립트 (LLM 없음, 순수 Python)

| 파일 | 역할 |
|------|------|
| `01_analyze.py` | DOM 추출 (서브페이지 병렬, 동적 UI·우클릭 메뉴 캡처, 정적 TTL 7일·동적 TTL 24h) |
| `02_generate.py` | 테스트 코드 scaffold 생성 |
| `02a_dialog.py` | Plan 심의 컨텍스트 초기화 |
| `03_lint.py` | flake8 검사 → step=reviewed 설정 |
| `03a_dialog.py` | 코드 리뷰 심의 컨텍스트 초기화 |
| `04_approve.py` | lint 리뷰 승인/반려 (종료코드 0=승인, 2=반려; auto_approve=true가 기본값) |
| `05_execute.py` | pytest 실행 (--only-failed, --no-report 플래그, 최대 4 workers) |
| `06_auto_heal.py` | 자동 힐링 패치 (8개 정적 패턴 + heal_stats 빈출 패턴) |
| `06_heal.py` | 실패 분석 (최대 3회 자동 패치) |
| `06a_dialog.py` | 힐링 심의 컨텍스트 초기화 |
| `_constants.py` | 파이프라인 종료코드 + VALID_TRANSITIONS + assert_valid_transition |
| `_excel_import.py` |  |
| `_import_commit.py` |  |
| `_import_validator.py` |  |
| `_paths.py` | 중앙 경로 상수 + read_state/write_state/update_state 원자적 I/O (FSM 전이 검증 내장) |
| `_pipeline_registry.py` | FSM 단일 소스: Step·ParallelStatus 상수, PIPELINE_STEP_DEFS, VALID_TRANSITIONS, make_initial_pipeline_state() 팩토리 |
| `_python.py` | .venv 경로 자동 감지 |
| `_state.py` |  |
| `_tc_connectors.py` | PRD URL·Confluence·Figma 소스 수집 |
| `_tc_credentials.py` | Confluence·Figma 자격증명 |
| `_tc_fetch.py` | 원격 문서 수집용 안전한 GET (SSRF 방어) |
| `_tc_generate.py` | TC 초안 생성 작업 (제한된 claude -p) |
| `_tc_html.py` | HTML·Confluence storage → markdown |
| `_tc_import_ops.py` |  |
| `_tc_library.py` | TC 라이브러리 저장소 (rev·이력·트리·필터) |
| `_tc_md_export.py` | TC 라이브러리 → 파이프라인 md 내보내기 |
| `_tc_model.py` | TC 스튜디오 케이스 모델·허용 값·검증 규칙 |
| `_tc_profiles.py` | TC 작성 프로필 저장소 |
| `_tc_prompt.py` | TC 생성 프롬프트·출력 스키마 |
| `_tc_review.py` | TC 초안 중복·커버리지 검토 도우미 |
| `_tc_source_watch.py` | 출처 버전 변경 추적 |
| `_tc_sources.py` | TC 생성용 소스 묶음 (PDF·DOCX·MD·TXT·붙여넣기 → markdown) |
| `_tc_template.py` | 엑셀 TC 템플릿 분석 (헤더·컬럼·드롭다운·No. 수식) |
| `_tc_trash.py` |  |
| `_tc_xlsx_export.py` | TC 라이브러리 → 템플릿 사본 xlsx + 무결성 검사 |
| `_tc_xlsx_import.py` | 엑셀 시트 → TC 라이브러리 케이스 |
| `_validators.py` | 대시보드 serve.py 입력 검증 헬퍼 (부작용 없이 재사용 가능하도록 분리) |
| `assert_guard.py` | 힐링 패치 후 assertion 약화 감지 (원본 대비 assertion 수·내용 비교, 경고 출력) |
| `check_pending_approve.py` | 훅: 승인 대기 상태 확인 (hook_utils.check_state) |
| `check_pending_discuss.py` | 훅: 토론 대기 상태 확인 |
| `check_pending_impl.py` | 훅: 구현 대기 상태 확인 |
| `check_pending_parallel.py` | 훅: 병렬 파이프라인 대기 상태 확인 |
| `check_pending_pipeline.py` | 훅: 단일 파이프라인 대기 상태 확인 |
| `check_pending_quick_heal.py` | 훅: 빠른 힐링 대기 상태 확인 |
| `coverage_matrix.py` | 커버리지 매트릭스 생성 (→ state/coverage.json) |
| `dom_helpers.js` | JS 공통 유틸 (isVisible·esc·getSelectorsSimple) — _js()가 자동 주입 |
| `flaky_detector.py` | Flaky Test 감지기 (run_history.json 분석 → state/flaky_tests.json) |
| `heal_utils.py` | 힐링 공용 유틸 (classify_error 7분류, append_lessons) |
| `hook_utils.py` | 훅 스크립트 공통 유틸: check_state() + remaining_steps_hint() — 레지스트리 기반 잔여 단계 지시문 생성 |
| `jira_reporter.py` | 테스트 실패 시 Jira 이슈 자동 생성 (스크린샷/영상 첨부 포함, config/jira_config.json 설정) |
| `parse_cases.py` | tc_*.md 파싱 (data_key: {프로덕트}.{데이터셋}) |
| `report_html.py` | HTML 리포트 생성 (단일/병렬 공통) |
| `result_parser.py` | pytest JSON 리포트 파싱 (단일/병렬 공유) |
| `structured_log.py` | 구조화 로그 (JSON Lines → logs/structured.jsonl) |
| `sync_test_data.py` | test_data/{프로덕트}.json 데이터셋 동기화 |
| `team_approve.py` | 팀 토론 승인 (터미널용) |
| `team_discuss.py` | 팀 토론 초기화 |
| `update_directory.py` | doc/reference/DIRECTORY.md 자동 생성 (이 파일) |

## parallel/ — 병렬 파이프라인 스크립트

| 파일 | 역할 |
|------|------|
| `99_merge.py` | pytest 실행 + 통합 리포트 + 힐링 루프 |

## testcases/ — 케이스 파일 (tc_*.md) — 그룹별 서브폴더

| 그룹 | TC 수 | 최근 실행 결과 |
|------|-------|---------------|
| `api_demo/` | 1개 | 0/1 (0%) |
| `customer_login/` | 2개 | 4/4 (100%) |
| `partner_login/` | 2개 | 4/4 (100%) |
| `tc_studio_demo/` | 8개 | - |

## tests/ — 테스트 산출물 (생성 코드·리포트·스크린샷)

### tests/generated/ — Claude Code가 작성한 테스트 코드

| 그룹 | 생성 파일 수 | 최근 실행 결과 |
|------|------------|---------------|
| `api_demo/` | 1개 | 0/1 (0%) |
| `customer_login/` | 2개 | 4/4 (100%) |
| `partner_login/` | 2개 | 4/4 (100%) |
| `tc_studio_demo/` | 5개 | - |

| 경로 | 역할 |
|------|------|
| `tests/reports/` | HTML 리포트 (pytest 실행 결과) |
| `tests/screenshots/` | 실패 시 스크린샷 (conftest.py 기반 자동 캡처) |
| `tests/conftest.py` | pytest 전역 픽스처 |
| `tests/unit/` | 저장소 자체 단위 테스트 (`pytest`로 실행). 영역별 하위 폴더 ↓ |
| `tests/unit/pipeline/` | 파이프라인 단계·FSM 전이·상태 저장·힐링·병합 |
| `tests/unit/hooks/` | `check_pending_*` 훅 |
| `tests/unit/core/` | TC/결과 파서, test_data 부트스트랩, 문서↔레지스트리 동기화 |
| `tests/unit/dashboard/` | 대시보드 API·보안·리포트 관리 |
| `tests/unit/import_studio/` | Import Studio 백엔드·계약·프로필 (+ `fixtures/`) |

## agents/ — 사수-부사수 에이전트 시스템 (페르소나·교훈·대시보드)

| 파일/폴더 | 역할 |
|-----------|------|
| `IDENTITY.md` | 사수/부사수 페르소나 (말투·성격) |
| `SOUL.md` | 팀 원칙과 가치관 |
| `team_charter.md` | 팀 헌장 (협업 규칙·역할 정의) |
| `team_notes.md` | 승인된 팀 결정사항 |
| `lessons_learned.md` | 큐레이션된 실수 패턴 (수동 관리, 힐링 전 참조) |
| `lessons_learned_auto.md` | 자동 기록 힐링 로그 (heal_utils.py 자동 추가) |
| `dialog.json` | 팀 토론 대화 로그 |
| `roles/senior.md` | 사수 행동 지침 (상세) |
| `roles/junior.md` | 부사수 행동 지침 (상세) |
| `dashboard/serve.py` | 대시보드 로컬 서버 (포트 8766) |
| `dashboard/index.html` | 파이프라인 모니터링 대시보드 UI |

## state/ — 런타임 상태 파일 (파이프라인 실행 중 자동 생성·갱신)

| 파일 | 역할 |
|------|------|
| `coverage.json` | 커버리지 매트릭스 (coverage_matrix.py 생성) |
| `discuss.json` | 팀 토론 상태 |
| `heal_stats.json` | 힐링 오류 패턴별 빈도 카운터 (06_heal.py 자동 갱신) |
| `import_profiles.json` | 런타임 생성 |
| `parallel.json` | 병렬 파이프라인 상태 |
| `parallel_contexts.json` | 런타임 생성 |
| `parallel_plan.json` | 런타임 생성 |
| `pipeline.json` | 단일 파이프라인 상태 (FSM step 전이 검증 포함) |
| `quick.json` | 빠른 실행 상태 |
| `run_history.json` | 실행 이력 (매 실행 시 자동 append) |
| `dom_cache/` | 서브페이지 DOM 스냅샷 캐시 (URL MD5 해시 키) |

## config/ — 설정 파일 (URL 매핑·테스트 입력값)

| 파일 | 역할 |
|------|------|
| `pages.json` | 페이지명 → URL 매핑 (키 = testcases/ 하위 폴더명) |
| `test_data.json` | 테스트 입력값 (하드코딩 금지, 키 = 그룹명) |

## prompts/ — 심의 Agent 프롬프트 템플릿

| 파일 | 역할 |
|------|------|
| `plan_deliberation.md` | 02a 심의 — plan 수립 |
| `review_deliberation.md` | 03a 심의 — 코드 리뷰 |
| `heal_deliberation.md` | 06a 심의 — 힐링 패치 |
| `parallel_subagent.md` | 병렬 subagent 코드 생성 |
| `team_discussion.md` | 팀 토론 멀티라운드 |
| `examples/` | few-shot 예시 JSON (plan_good, plan_bad, heal_patch) |

## .claude/skills/ — 스킬 프레임워크 (SKILL.md 표준, Claude Code 참조용)

| 스킬 | 역할 |
|------|------|
| `browser-qa/` | 배포 후 시각 검증, 4단계 QA 플로우 (ECC) |
| `heal-patterns/` | 힐링 오류 유형별 패치 전략 가이드라인 (qa-native) |
| `image-to-code/` |  |
| `playwright-best-practices/` | Python Playwright 정적 베스트프랙티스 (qa-native) |
| `python-testing/` | pytest 픽스처·파라미터화·mocking 전략 (ECC) |
| `skillify/` | 반복 패턴 → heal-patterns/lessons_learned 공식 등록 (qa-native) |
| `taste-skill/` |  |
| `verify/` | 패치 후 05_execute 기반 3단계 증거 검증 (qa-native) |
| `web-design-guidelines/` |  |

## doc/ — 문서 (사람용·에이전트 on-demand 참조)

| 파일 | 역할 |
|------|------|
| `README.md` | 문서 안내 |
| `design/PROJECT_OVERVIEW.md` | QA-Native — 아키텍처 문서 |
| `design/tc-studio/TC_AUTHORING_ELEMENT_SPEC.md` | TC 스튜디오 요소 동작 명세 |
| `design/tc-studio/TC_AUTHORING_PRD.md` | PRD: TC Authoring Studio (문서 기반 테스트케이스 작성·관리) |
| `development/DOCUMENTATION_REVIEW.md` | 문서 정리 기록 |
| `development/tc-studio/IMPORT_STUDIO_INTEGRATION_REVIEW.md` | Import Studio를 TC 스튜디오에 통합하는 방안 |
| `development/tc-studio/TC_AUTHORING_HANDOFF.md` | TC Authoring Studio 개발 인수인계 |
| `development/tc-studio/TC_AUTHORING_IMPLEMENTATION_REPORT.md` | TC Authoring Studio 구현 보고 |
| `development/tc-studio/TC_AUTHORING_ROADMAP.md` | TC Authoring Studio 개발 로드맵 |
| `development/tc-studio/plans/2026-09-29-tc-authoring-phase1.md` | TC Authoring Studio Phase 1 Implementation Plan — 라이브러리 + 엑셀 왕복 |
| `development/tc-studio/plans/2026-09-30-import-integration.md` | Import 기능의 TC 스튜디오 통합 구현 계획 |
| `development/tc-studio/plans/2026-09-30-tc-authoring-phase2.md` | TC Authoring Studio Phase 2 Implementation Plan — 파일 소스 · 생성 작업 · 초안 검토 |
| `development/tc-studio/plans/2026-09-30-tc-authoring-phase3.md` | TC Authoring Studio Phase 3 Implementation Plan — Confluence · Figma · PRD URL · 출처 버전 추적 |
| `development/tc-studio/plans/2026-09-30-tc-authoring-phase4.md` | TC Authoring Studio Phase 4 Implementation Plan — md 내보내기 (파이프라인 연결) |
| `guides/SCRIPTS_GUIDE.md` | 파이썬 파일 실행 가이드 |
| `guides/TEST_CASE_GUIDE.md` | QA-Native 테스트 케이스 작성 가이드 |
| `guides/tc-studio/TC_AUTHORING_USER_GUIDE.md` | TC 스튜디오 사용자 설명서 |
| `guides/tc-studio/templates/회원등록_기획예시.md` | 회원 등록 기획 예시 |
| `operations/HEALING_GUIDE.md` | 힐링 가이드 |
| `operations/TEAM_DISCUSSION.md` | 팀 자유 토론 파이프라인 |
| `reference/API_REFERENCE.md` | API & CLI 레퍼런스 |
| `reference/DIRECTORY.md` | 디렉토리 구조 |
| `reference/PIPELINE_STATE.md` | state/pipeline.json 구조 |
| `reference/PROMPTS_REFERENCE.md` | 프롬프트 템플릿 레퍼런스 |

## 기타

| 경로 | 역할 |
|------|------|
| `knowledge/` | QA 지식 베이스 (체크리스트·팀 내규) |
| `templates/` | 문서 템플릿 (TC·리포트·이슈) |
| `logs/` | 실행 로그 (run_qa.txt, run_parallel.txt, structured.jsonl 등) |
| `reports/issues/` | 이슈 추적 파일 (ISSUE-{날짜}-{번호}.md) |
