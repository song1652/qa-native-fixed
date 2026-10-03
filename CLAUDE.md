# QA Automation — Claude Code Native

> **독자**: Claude Code — 파이프라인 전체 실행 지침.
> 상세: [HEALING_GUIDE](doc/operations/HEALING_GUIDE.md), [TEAM_DISCUSSION](doc/operations/TEAM_DISCUSSION.md), [PIPELINE_STATE](doc/reference/PIPELINE_STATE.md), [DIRECTORY](doc/reference/DIRECTORY.md), [SCRIPTS_GUIDE](doc/guides/SCRIPTS_GUIDE.md)

## 행동 원칙
- 이미 읽은 파일은 재읽기 금지
- 독립적 도구 호출은 반드시 병렬 실행
- 완료 보고 시 이미 설명한 내용 반복 금지
- **state/pipeline.json 수동 덮어쓰기 금지**: `heal_count` 등 누적 필드가 리셋됨. 반드시 스크립트(06_heal 등)를 통해 상태 변경. `write_state()`/`update_state()`가 FSM 전이 규칙을 자동 검증
- **상태 수정은 `update_state(path, mutator)` 사용**: `read_state → 수정 → write_state` 패턴은 RMW 경쟁이 발생한다. 상태 필드를 변경하는 코드는 `update_state(path, lambda s: {**s, "field": value})` 원자적 패턴을 사용 (P43)
- **Sequential Thinking 우선 사용**: 판단이 필요한 모든 단계(심의·코드 완성·힐링)에서 `mcp__sequential-thinking__sequentialthinking`을 먼저 호출해 단계적으로 추론한 뒤 실행한다

API 호출 없이 Claude Code 자체가 LLM 역할을 수행하는 QA 자동화 시스템.
모든 단계 결과는 `state/pipeline.json`에 누적되며, Claude Code가 순서대로 직접 실행한다.

## 절대 규칙
- `anthropic`, `langchain`, `openai` 등 외부 LLM SDK import 절대 금지. API 키 사용 금지
- 모든 단계 결과는 반드시 state/pipeline.json에 저장 후 다음 단계 진행
- 코드 생성은 Claude Code가 직접 파일로 작성 (문자열 출력 후 저장 아님)
- **레지스트리 상수 사용**: pipeline step·parallel status 값은 반드시 `scripts/_pipeline_registry.py`의 `Step.*` / `ParallelStatus.*` 상수를 사용. 문자열 리터럴 하드코딩 금지 (예: `"init"` 대신 `Step.INIT`, `"heal_needed"` 대신 `ParallelStatus.HEAL_NEEDED`) (P44/P45)
- **lessons_learned 필수 참조**: 코드 작성·리뷰·힐링 전 [lessons_learned.md](agents/lessons_learned.md) 확인 (큐레이션된 패턴). 자동 기록 로그는 [lessons_learned_auto.md](agents/lessons_learned_auto.md)
- **lessons_learned 즉시 기록**: 코드 패치(힐링·lint 수정·생성 오류 등) 시 교훈을 lessons_learned.md에 수동 기록 (자동 기록은 heal_utils.py가 _auto.md에 처리). 중복 시 생략
- **테스트 함수명**: 반드시 영문 snake_case `test_{english_snake_case}` (한글 제목도 영어로 번역)
- **테스트 파일은 자체 완결**: 공유 헬퍼 파일 생성 금지. BASE_URL·import·상수를 각 파일에 직접 포함
- **tc_*.md 1개 = 테스트 파일 1개 = 테스트 함수 1개**
- **파일명 규칙 (단일/병렬 공통)**: `tc_{번호}_{english_snake_case}.py` 또는 `tc_{그룹코드}_{번호}_{english_snake_case}.py` (예: `tc_01_login_success.py`, `tc_CL_01_customer_login_empty.py`)

## 설정 파일

| 파일 | 용도 |
|------|------|
| [pages.json](config/pages.json) | URL 매핑 (string/object 혼용). 키 = testcases/ 폴더명 |
| [test_data/{product}.json](test_data/) | 프로덕트별 테스트 입력값 (gitignored). `_paths.load_test_data()`로 머지 로드 |
| [test_data/{product}.example.json](test_data/) | 빈 템플릿 (git 추적, 팀 공유) |
| [run_history.json](state/run_history.json) | 실행 이력 (자동 append) |

테스트케이스: YAML frontmatter + Markdown 본문. 상세 스키마 → [SCRIPTS_GUIDE](doc/guides/SCRIPTS_GUIDE.md)

## 실행 원칙
- **병렬 우선**: 독립 작업은 반드시 동시 실행
- **페르소나는 힐링 심의(06a)에만 적용**: 02a(계획)·03a(리뷰)는 Claude Code가 체크리스트 기반으로 직접 plan/review 생성. 06a(힐링)만 사수/부사수 진단→패치 구조 유지 (P64)
- **컨텍스트 주입**: `*_dialog.py`가 출력하는 `DELIBERATION_CONTEXT` JSON을 프롬프트에 직접 포함. 02a/03a는 lessons_learned+DOM+코드만 포함 (team_charter/persona 제외)

## 훅 레이어 (UserPromptSubmit 자동 주입)

`.claude/settings.json`에 등록된 `check_pending_*.py` 6개가 매 프롬프트 제출 시 자동 실행됩니다.
파이프라인 상태가 특정 조건에 해당하면 stdout에 지시문을 출력하여 Claude 컨텍스트에 주입합니다.

| 훅 스크립트 | 트리거 조건 | 주입 내용 |
|---|---|---|
| `check_pending_pipeline.py` | `pipeline.json` `step=`**`Step.INIT`** + url 있음 | 단일 파이프라인 시작 지시 + 레지스트리 기반 잔여 단계 목록 |
| `check_pending_approve.py` | `pipeline.json` `step=`**`Step.REVIEWED`** + 미실행 | 테스트 실행 지시 + 잔여 단계 목록 |
| `check_pending_parallel.py` | `parallel.json` `status=`**`ParallelStatus.READY`** | subagent 실행 지시 + PARALLEL_SUBAGENT_CONTEXTS |
| `check_pending_quick_heal.py` | `quick.json` `status=`**`ParallelStatus.HEAL_NEEDED`** | HEAL_SUBAGENT_CONTEXTS 주입 |
| `check_pending_discuss.py` | `discuss.json` `step=pending` | 팀 토론 진행 지시 |
| `check_pending_impl.py` | `pending_impl.json` 승인 항목 있음 | 구현 요청 주입 |

> `workflow_status`가 `failed`·`cancelled`·`interrupted`·`timed_out`·`incomplete`이면 훅은 잔존 단계의 실행 지시를 주입하지 않습니다. 중단된 작업은 새 실행 진입점에서 시작합니다.
> 진행 가능한 작업에 훅이 지시문을 주입하면 해당 파이프라인 단계를 실행합니다.
> 트리거 조건 값은 모두 `_pipeline_registry.py` 레지스트리 상수 기반 (P44).

## 스킬 프레임워크 & OMC 적용

[`.claude/skills/`](.claude/skills/)에 정적 베스트프랙티스를 SKILL.md 표준으로 관리. 동적 빈도 데이터는 `state/heal_stats.json` (실행 중 생성)에 기록되며, [06a_dialog.py](scripts/06a_dialog.py)가 Top 5 빈출 패턴을 DELIBERATION_CONTEXT에 자동 주입.

| 스킬 | 경로 | 용도 |
|------|------|------|
| Playwright Best Practices | [SKILL.md](.claude/skills/playwright-best-practices/SKILL.md) | 테스트 코드 작성 시 셀렉터·대기 전략 참조. React SPA 이벤트·Tip팝업·파일업로드 포함 |
| Heal Patterns | [SKILL.md](.claude/skills/heal-patterns/SKILL.md) | 힐링 패치 전략, 오류 유형별 수정 패턴. nativeInputValueSetter·SPA클릭 포함 |
| Browser QA (ECC) | [SKILL.md](.claude/skills/browser-qa/SKILL.md) | 배포 후 시각 검증, 4단계 QA 플로우 |
| Python Testing (ECC) | [SKILL.md](.claude/skills/python-testing/SKILL.md) | pytest 픽스처·파라미터화·mocking 전략 |
| Verify | [SKILL.md](.claude/skills/verify/SKILL.md) | 패치 후 05_execute 기반 증거 검증. "됐을 것 같다" 금지 |
| Skillify | [SKILL.md](.claude/skills/skillify/SKILL.md) | 반복 패턴 → heal-patterns/lessons_learned 공식 등록 |

파이프라인 단계별 OMC 스킬:

| 단계 | 명령 | 참조 SKILL.md | 핵심 |
|------|------|--------------|------|
| 코드 완성 (02_generate 이후) | `/oh-my-claudecode:ultrapilot` | `playwright-best-practices`, `python-testing` | scaffold 파일을 agent별 파티셔닝, dom_info+lessons_learned+SKILL.md 참조 |
| 린트 수정 (03_lint 이후) | Agent tool 직접 병렬 호출 | `python-testing` | lint 이슈 파일별로 Agent 동시 실행 |
| 힐링 루프 (05_execute 실패 시) | `/oh-my-claudecode:ultraqa` | `heal-patterns`, `browser-qa` | 06_heal → 06_auto_heal → (잔여) 06a_dialog 순서 준수. 검증 실패 없이 남은 Locator 후보에 최대 3회. exit 5·recovery_stopped면 즉시 중단. 패치마다 lessons_learned 기록 |
| 병렬 공통 심의 (02a_parallel_dialog 후) | Agent tool 직접 | `playwright-best-practices`, `python-testing` | parallel_plan.json 저장 후 subagent spawn |
| 패치 후 검증 | `/oh-my-claudecode:verify` | `verify` | 힐링 패치 직후 05_execute 증거 확인. 통과 전 완료 선언 금지 |
| 패턴 등록 (세션 종료 전) | `/oh-my-claudecode:skillify` | `skillify` | 반복 패턴 발견 시 heal-patterns 또는 lessons_learned에 등록 |
| 슬롭 정리 (전체 통과 후) | `/oh-my-claudecode:ai-slop-cleaner` | — | 힐링/병렬 완료 후 생성 코드 품질 정리. 동작 변경 없이 중복·죽은 코드 제거 |

## 실행 안전 정책 (1·2·3차 공통)

- **1차 — 실행 소유권·취소**: 대시보드 단일·병렬·빠른 실행과 초기화는 공통 실행 잠금으로 보호한다. `QA_RUN_ID`·`QA_WORKFLOW_ID`를 자식 단계에 유지한다. `state/runs/{run_id}/execution_result.json`의 소유 결과만 사용하며, 소유권이 바뀐 이전 작업은 최신 상태를 갱신하지 않는다. worker는 모든 단계에 동일한 `--state-path`를 전달한다.
- **2차 — 종료 상태·증거**: 대시보드 재시작 후 실행을 재확인한다. 프로세스 종료만으로 PASS를 만들지 않는다. `workflow_status`의 실패·취소·중단·시간 초과·미완료는 다음 단계 훅을 억제한다. pytest 호출별 `invocation_id`로 리포트·화면·Trace를 구분하고 기존 실행의 증거를 덮어쓰거나 폴더 전체를 초기화하지 않는다.
- **3차 — 제한된 복구**: setup·call·teardown·수집 오류를 모두 판정한다. 측정된 실패가 모두 Locator 오류이고 pytest가 정상 종료(0·1)한 경우에만 자동 복구한다. 기대값·브라우저·세션·통신·설정·일반 타임아웃·중단·알 수 없는 오류는 멈추고 원인을 안내한다.
- **실패 자체는 재실행 권한이 아니다**: 진단용 `--lf`·전체 pytest 재실행을 하지 않는다. `rerunfailures`는 비활성화한다. 알려진 일시적 통신 오류의 DOM 읽기만 최초 호출 포함 최대 3회 재시도하며 클릭·입력·저장 동작은 반복하지 않는다.
- **새 DOM 필수**: 자동 복구 전 현재 URL에서 캐시를 무시하고 DOM을 수집한다. 수집 실패·빈 DOM이면 검증 전에 중단한다. 이전 DOM·다른 실행의 스크린샷으로 대체하지 않는다.
- **복구 검증 실패 즉시 중단**: 변경 파일당 한 번 검증하며 첫 미통과·크래시·타임아웃에서 이번 자동 패치의 파일을 원래 바이트로 복원한다. `06_auto_heal` 종료코드 **5** 또는 `recovery_stopped=true` 이후 다른 전략·파일·배치·Agent 패치·`06a_dialog`·`05_execute`·`99_merge`를 추가 실행하지 않는다. SIGTERM·KeyboardInterrupt도 검증 중 임시 변경을 복원한다. SIGKILL은 복원 코드를 실행할 수 없다.

상세 CLI·종료코드 → [힐링 가이드](doc/operations/HEALING_GUIDE.md).

## 힐링

힐링 완료 필수: (1) 코드 패치 (2) [lessons_learned.md](agents/lessons_learned.md)에 교훈 기록 (중복 시 생략, 자동 로그는 [_auto.md](agents/lessons_learned_auto.md)에 별도 기록) (3) 재실행 통과 확인.
lint 수정·코드 생성 시 반복 오류도 동일하게 lessons_learned.md에 즉시 기록.
오류 유형별 패치 전략 → [Heal Patterns SKILL.md](.claude/skills/heal-patterns/SKILL.md). MCP 시각 검증 → [HEALING_GUIDE](doc/operations/HEALING_GUIDE.md)
**힐링 1회차부터 Sequential Thinking 필수**: 오류 유형과 관계없이 힐링 진입 즉시 `mcp__sequential-thinking__sequentialthinking`을 호출해 원인을 단계적으로 추론한 뒤 패치 전략을 결정한다.

**힐링 배치 병렬화**: 06_heal.py / 99_merge.py가 `HEAL_SUBAGENT_CONTEXTS`를 출력하면, 각 배치를 Agent tool로 **동시에** 실행. 배치당 최대 6건 (heal_utils.HEAL_BATCH_SIZE). 단일/병렬/빠른 실행 모두 동일한 출력 형식 사용.

## 단일 파이프라인 (단일 URL)

```
01_analyze → 02a_dialog → [심의] → 02_generate → 03_lint → 03a_dialog → [심의] → 04_approve → 05_execute → 06_heal → 06_auto_heal → [exit 1시] → 06a_dialog → [심의] → [Agent 패치] → assert_guard → [힐링 루프]
```

1. `python scripts/01_analyze.py` — DOM 추출 (메인 + 서브페이지 병렬 수집, React 컴포넌트 포함)
2. `python scripts/02a_dialog.py` → [심의] [plan_deliberation.md](prompts/plan_deliberation.md) + ctx
3. `python scripts/02_generate.py` — scaffold 생성 후 plan 기반 개별 완성
4. `python scripts/03_lint.py` — flake8 + step=reviewed 설정
5. `python scripts/03a_dialog.py` → [심의] [review_deliberation.md](prompts/review_deliberation.md) + ctx
6. `python scripts/04_approve.py` — QA 리드 승인 게이트. 종료코드 0: 승인 / **4**: 반려→재작성 (EXIT_REJECTED=4, P59에서 EXIT_HEAL_EXCEEDED=2와 충돌 해소) (config/pipeline.json의 auto_approve=true가 기본값이라 보통 즉시 승인됨; "대시보드 대기" 폴백은 UI가 없는 데드엔드라 #26에서 제거)
7. `python scripts/05_execute.py` — pytest 실행
8. `python scripts/06_heal.py` — 종료코드 0: 실패 없음·대상 단계 아님 / 10: 복구 후보 준비 / 2: 복구 불가·반복·초과 등으로 중단
9. `python scripts/06_auto_heal.py` — 결정적 패턴 자동 패치 (Agent 호출 전). 종료코드 0: 검증 통과·잔여 없음 / 1: 검증 실패 없이 미수정 후보 남음→10번으로 / 3: 스킵 / **5: 원본 복원·자동 복구 중단**
10. (exit 1시) `python scripts/06a_dialog.py` → [심의] [heal_deliberation.md](prompts/heal_deliberation.md) + ctx
11. (exit 1시) Agent 패치 → `python scripts/assert_guard.py` 실행

> **실행 순서 근거**: 06_auto_heal은 결정적 패턴 매칭으로 쉬운 케이스를 먼저 제거한다.
> 06a_dialog(심의)는 자동 수정 후 **남은 어려운 실패만** 컨텍스트에 담으므로 Agent 지시가 더 정확해진다.

> **리포트/스크린샷/Trace 규칙 (필수)**:
> - **첫 실행 포함 모든 실행은 `--no-report`로 실행**. HTML 리포트는 전체 통과 확인 후 마지막 1회 생성하고 실패 진단 화면·Trace는 각 실행에서 보존.
> - 실행 순서: `05_execute.py --no-report` → `06_heal.py` → 패치 → `05_execute.py --no-report` → ... → 전체 통과 확인 → `05_execute.py` (리포트 생성). 복구 검증 실패·exit 5이면 그 시점에서 중단
> - **허용된 패치 확인 시**: `05_execute.py --no-report --only-failed`로 이전 실패만 선택 가능. exit 5·recovery_stopped·종료된 workflow에서는 재실행 금지
> - `--no-report`는 HTML 생성을 생략하며 실패 진단 증거는 계속 저장한다. 기존 증거 폴더는 초기화하지 않는다. 실행·호출별 접두어로 분리한다.
> - **Trace**: 실패한 TC에 한해 `tests/traces/{run_id}__{invocation_id}__{group}__{test}.zip` 자동 생성. 힐링 시 `meta.json`의 `trace_path` 참조. 뷰어: `npx playwright show-trace <파일>.zip`

> **슬롭 정리 (선택, 전체 통과 후)**:
> 힐링을 여러 번 거친 파일에 중복 패치·죽은 코드가 쌓였다면 리포트 생성 전 실행:
> `/oh-my-claudecode:ai-slop-cleaner tests/generated/{group}/`

## 병렬 파이프라인 (다중 URL)

```
run_qa_parallel.py → 02a_parallel_dialog → [공통 심의] → subagents × N → 99_merge.py
```

1. `python run_qa_parallel.py` — testcases/ 스캔 + DOM 분석 → `state/parallel_contexts.json` 생성
2. `python parallel/02a_parallel_dialog.py` → DELIBERATION_CONTEXT 출력
   → [공통 심의]: 전체 그룹 테스트 전략 수립 (사수·부사수 내부 시뮬레이션)
   → 결과를 `state/parallel_plan.json` 에 저장 — [parallel_plan_deliberation.md](prompts/parallel_plan_deliberation.md) 참조
3. `state/parallel_contexts.json` 읽기 — 구조: `{ shared_context_paths: {...}, subagents: [...] }`
4. `shared_context_paths`의 파일들(`parallel_plan.json` 포함)은 각 subagent가 직접 읽음 (토큰 절감)
5. `subagents[]` 배열의 각 항목을 Agent tool로 **동시에** 실행 — [parallel_subagent.md](prompts/parallel_subagent.md) 참조
6. 모든 subagent 완료 후 `python parallel/99_merge.py`
7. Locator 후보만 단일과 동일하게 복구 ([HEALING_GUIDE](doc/operations/HEALING_GUIDE.md) 참조). 검증 실패 없이 남은 후보에 최대 3회. 검증 실패·exit 5·recovery_stopped면 원본 복원 후 즉시 중단
8. **슬롭 정리 (선택, 전체 통과 후)**: 여러 subagent가 생성한 파일의 스타일 불일치·중복 정리
   `/oh-my-claudecode:ai-slop-cleaner tests/generated/`

## 팀 토론

`python run_team.py --topic "주제"` → 사수/부사수 멀티라운드 토론 → 대시보드 승인/반려.
상세 → [TEAM_DISCUSSION](doc/operations/TEAM_DISCUSSION.md)

## 참조

- state/pipeline.json 스키마 → [PIPELINE_STATE](doc/reference/PIPELINE_STATE.md)
- 디렉토리 구조 → [DIRECTORY](doc/reference/DIRECTORY.md)
- 스크립트 인자/옵션 상세 → [SCRIPTS_GUIDE](doc/guides/SCRIPTS_GUIDE.md)
- CLI 옵션 + API 엔드포인트 → [API_REFERENCE](doc/reference/API_REFERENCE.md)
- 프롬프트 템플릿 입출력 → [PROMPTS_REFERENCE](doc/reference/PROMPTS_REFERENCE.md)


## 사용자 문서 관리

- 현재 사용법: [HTML 사용자 가이드](doc/guides/USER_GUIDE.html), [TC 스튜디오 설명서](doc/guides/tc-studio/TC_AUTHORING_USER_GUIDE.html). TC 스튜디오는 작성부터 내보내기까지만 설명한다.
- UI·버튼·문구 변경 시 해당 `doc/guides/` Markdown 원본과 실제 화면 캡처를 함께 갱신한다. 생성 HTML은 직접 수정하지 않고 `python3 scripts/build_user_guides.py`로 갱신한다.
- 이미지는 `doc/images/`에 저장하고 [촬영 기준](doc/images/README.md)에 날짜·화면 크기·실제 화면/예시 응답 여부를 기록한다. 성공 결과나 상태를 임의로 넣은 이미지를 실제 실행 증거로 설명하지 않는다.
- 문서 수정 후 `python3 scripts/build_user_guides.py --check`와 문서 테스트를 확인한다. 설치·갱신 명령은 [문서 안내](doc/README.md#가이드와-이미지-갱신-규칙)를 따른다.
- API·상태·운영 계약은 Markdown 레퍼런스에서 관리한다. 완료된 PRD·디자인 목업·개발 계획은 다시 만들지 않는다.
