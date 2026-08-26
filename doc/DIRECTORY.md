# 디렉토리 구조

> **자동 생성** — `python scripts/update_directory.py` | 마지막 갱신: 2026-05-03 20:04
> 최근 실행: 2026-04-27 17:23 | single | heroku | 10/10 | heal:1

> 역할 설명 수정: `scripts/update_directory.py` 내 `SCRIPT_DESCRIPTIONS` / `FOLDER_DESCRIPTIONS` 편집.

---

## 루트

| 파일 | 역할 |
|------|------|
| `_bootstrap.py` | 프로젝트 진입점 공통 경로 설정 (루트 스크립트가 import) |
| `run_qa.py` | 단일 파이프라인 실행 엔트리포인트 (기본: headless Claude 자동 실행, `--no-auto` 시 안내만 출력) |
| `run_qa_parallel.py` | 병렬 파이프라인 실행 엔트리포인트 (기본: headless Claude 자동 실행, `--no-auto` 시 안내만 출력) |
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
| `06_auto_heal.py` | 자동 힐링 패치 (7개 정적 패턴 + heal_stats 빈출 패턴) |
| `06_heal.py` | 실패 분석 (최대 3회 자동 패치) |
| `06a_dialog.py` | 힐링 심의 컨텍스트 초기화 |
| `_constants.py` | 파이프라인 종료코드 + VALID_TRANSITIONS + assert_valid_transition |
| `_paths.py` | 중앙 경로 상수 + read_state/write_state/update_state 원자적 I/O (FSM 전이 검증 내장) |
| `_pipeline_registry.py` | FSM 단일 소스: Step·ParallelStatus 상수, PIPELINE_STEP_DEFS(메타), VALID_TRANSITIONS/VALID_PARALLEL_TRANSITIONS, make_initial_pipeline_state() 팩토리 (P35·P39·P41) |
| `_python.py` | .venv 경로 자동 감지 |
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
| `hook_utils.py` | 훅 스크립트 공통 유틸: `check_state()` + `remaining_steps_hint(from_step)` — 레지스트리 기반 잔여 단계 지시문 자동 생성 (P44) |
| `parse_cases.py` | tc_*.md 파싱 |
| `report_html.py` | HTML 리포트 생성 (단일/병렬 공통) |
| `result_parser.py` | pytest JSON 리포트 파싱 (단일/병렬 공유) |
| `structured_log.py` | 구조화 로그 (JSON Lines → logs/structured.jsonl) |
| `sync_test_data.py` | test_data.json 동기화 |
| `team_approve.py` | 팀 토론 승인 (터미널용) |
| `team_discuss.py` | 팀 토론 초기화 |
| `update_directory.py` | doc/DIRECTORY.md 자동 생성 (이 파일) |

## parallel/ — 병렬 파이프라인 스크립트

| 파일 | 역할 |
|------|------|
| `99_merge.py` | pytest 실행 + 통합 리포트 + 힐링 루프 |

## testcases/ — 케이스 파일 (tc_*.md) — 그룹별 서브폴더

새 프로젝트 대상 TC 작성 후 그룹별 서브폴더로 관리. 폴더명 = `pages.json` 키와 일치.

## tests/ — 테스트 산출물 (생성 코드·리포트·스크린샷·Trace)

### tests/generated/ — Claude Code가 작성한 테스트 코드

새 프로젝트 대상 TC 생성 후 채워짐.

| 경로 | 역할 |
|------|------|
| `tests/reports/` | HTML 리포트 (pytest 실행 결과) |
| `tests/screenshots/` | 실패 시 스크린샷 + meta.json (conftest.py 기반 자동 캡처) |
| `tests/traces/` | 실패 시 Playwright Trace (`retain-on-failure`). 뷰어: `npx playwright show-trace <파일>.zip` |
| `tests/conftest.py` | pytest 전역 픽스처 (tracing 포함) |
| `tests/test_99_merge.py` | 99_merge.py FSM·quick 모드 크래시·배치 힐링 (P41) |
| `tests/test_analyze_state.py` | 01_analyze.py state 저장 검증 |
| `tests/test_approve_gate.py` | 04_approve.py 원자적 RMW·rejection_count 증가 (P43) |
| `tests/test_auto_heal.py` | 06_auto_heal.py 자동 패치 패턴 |
| `tests/test_check_pending_hooks.py` | check_pending 4개 트리거 조건·remaining_steps_hint 레지스트리 기반 (P44) |
| `tests/test_core_parsers.py` | tc_*.md 파서 유닛 테스트 |
| `tests/test_dashboard_state_wiring.py` | 대시보드 상태 배선 통합 |
| `tests/test_doc_registry_sync.py` | PIPELINE_STATE.md·SCRIPTS_GUIDE.md ↔ 레지스트리 드리프트 감지 (P38) |
| `tests/test_fsm_transitions.py` | VALID_TRANSITIONS·VALID_PARALLEL_TRANSITIONS FSM 규칙 |
| `tests/test_generate_state.py` | 02_generate.py 원자적 RMW (P43) |
| `tests/test_headless_entrypoints.py` | headless 자동 실행 진입점 |
| `tests/test_heal_stats.py` | heal_stats.json 빈도 카운터 |
| `tests/test_lint_state.py` | 03_lint.py state 저장 검증 |
| `tests/test_pipeline_registry.py` | Step·ParallelStatus·make_initial_pipeline_state() 팩토리 (P39) |
| `tests/test_pipeline_registry_api.py` | /api/pipeline_registry 응답 구조·레지스트리 일관성 (P45) |
| `tests/test_serve_security.py` | 대시보드 보안·quick heal_count 리셋 (P42) |
| `tests/test_test_data_bootstrap.py` | test_data.json 부트스트랩 |
| `tests/test_update_state.py` | update_state() 원자성·FSM 검증 |

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
| `parallel.json` | 병렬 파이프라인 상태 |
| `parallel_contexts.json` | 병렬 파이프라인 subagent 컨텍스트 전체 (dom_info + test_cases + shared_paths). run_qa_parallel.py가 저장, headless Claude가 읽음 |
| `pipeline.json` | 단일 파이프라인 상태 (FSM step 전이 검증 포함) |
| `pipeline_new.json` | 런타임 생성 |
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
| `playwright-best-practices/` | Python Playwright 정적 베스트프랙티스 (qa-native) |
| `python-testing/` | pytest 픽스처·파라미터화·mocking 전략 (ECC) |
| `skillify/` | 반복 패턴 → heal-patterns/lessons_learned 공식 등록 (qa-native) |
| `verify/` | 패치 후 05_execute 기반 3단계 증거 검증 (qa-native) |

## doc/ — 문서 (사람용·에이전트 on-demand 참조)

| 파일 | 역할 |
|------|------|
| `DIRECTORY.md` | 디렉토리 구조 (이 파일, 자동 생성) |
| `PIPELINE_STATE.md` | state/pipeline.json 스키마 상세 |
| `HEALING_GUIDE.md` | 힐링 완료 체크리스트 + MCP 시각 검증 절차 |
| `SCRIPTS_GUIDE.md` | 스크립트 CLI 옵션·실행 방법 |
| `TEAM_DISCUSSION.md` | 팀 토론 파이프라인 상세 |
| `API_REFERENCE.md` | CLI 옵션 + 대시보드 API 엔드포인트 |
| `PROMPTS_REFERENCE.md` | prompts/ 템플릿 입출력 스키마 |
| `PROJECT_OVERVIEW.md` | 아키텍처 설계 문서 |

## 기타

| 경로 | 역할 |
|------|------|
| `knowledge/` | QA 지식 베이스 (체크리스트·팀 내규) |
| `templates/` | 문서 템플릿 (TC·리포트·이슈) |
| `logs/` | 실행 로그 (run_qa.txt, run_parallel.txt, run_qa_headless.txt, run_qa_parallel_headless.txt, structured.jsonl 등) |
| `reports/issues/` | 이슈 추적 파일 (ISSUE-{날짜}-{번호}.md) |
