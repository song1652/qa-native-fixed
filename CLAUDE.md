# QA Automation — Claude Code Native

> **독자**: Claude Code — 파이프라인 전체 실행 지침.
> 상세: [HEALING_GUIDE](doc/HEALING_GUIDE.md), [TEAM_DISCUSSION](doc/TEAM_DISCUSSION.md), [PIPELINE_STATE](doc/PIPELINE_STATE.md), [DIRECTORY](doc/DIRECTORY.md), [SCRIPTS_GUIDE](doc/SCRIPTS_GUIDE.md)

## 행동 원칙
- 이미 읽은 파일은 재읽기 금지
- 독립적 도구 호출은 반드시 병렬 실행
- 완료 보고 시 이미 설명한 내용 반복 금지
- **state/pipeline.json 수동 덮어쓰기 금지**: `heal_count` 등 누적 필드가 리셋됨. 반드시 스크립트(06_heal 등)를 통해 상태 변경. `write_state()`가 FSM 전이 규칙을 자동 검증
- **Sequential Thinking 우선 사용**: 판단이 필요한 모든 단계(심의·코드 완성·힐링)에서 `mcp__sequential-thinking__sequentialthinking`을 먼저 호출해 단계적으로 추론한 뒤 실행한다

API 호출 없이 Claude Code 자체가 LLM 역할을 수행하는 QA 자동화 시스템.
모든 단계 결과는 `state/pipeline.json`에 누적되며, Claude Code가 순서대로 직접 실행한다.

## 절대 규칙
- `anthropic`, `langchain`, `openai` 등 외부 LLM SDK import 절대 금지. API 키 사용 금지
- 모든 단계 결과는 반드시 state/pipeline.json에 저장 후 다음 단계 진행
- 코드 생성은 Claude Code가 직접 파일로 작성 (문자열 출력 후 저장 아님)
- **lessons_learned 필수 참조**: 코드 작성·리뷰·힐링 전 [lessons_learned.md](agents/lessons_learned.md) 확인 (큐레이션된 패턴). 자동 기록 로그는 [lessons_learned_auto.md](agents/lessons_learned_auto.md)
- **lessons_learned 즉시 기록**: 코드 패치(힐링·lint 수정·생성 오류 등) 시 교훈을 lessons_learned.md에 수동 기록 (자동 기록은 heal_utils.py가 _auto.md에 처리). 중복 시 생략
- **테스트 함수명**: 반드시 영문 snake_case `test_{english_snake_case}` (한글 제목도 영어로 번역)
- **테스트 파일은 자체 완결**: 공유 헬퍼 파일 생성 금지. BASE_URL·import·상수를 각 파일에 직접 포함
- **tc_*.md 1개 = 테스트 파일 1개 = 테스트 함수 1개**
- **파일명 규칙 (단일/병렬 공통)**: `tc_{번호}_{english_snake_case}.py` (예: `tc_01_login_success.py`)

## 설정 파일

| 파일 | 용도 |
|------|------|
| [pages.json](config/pages.json) | URL 매핑 (string/object 혼용). 키 = testcases/ 폴더명 |
| [test_data.json](config/test_data.json) | 테스트 입력값. 하드코딩 금지 |
| [run_history.json](state/run_history.json) | 실행 이력 (자동 append) |

테스트케이스: YAML frontmatter + Markdown 본문. 상세 스키마 → [SCRIPTS_GUIDE](doc/SCRIPTS_GUIDE.md)

## 실행 원칙
- **병렬 우선**: 독립 작업은 반드시 동시 실행
- **심의 Agent 1회 호출**: 사수/부사수를 단일 agent가 내부 시뮬레이션
- **컨텍스트 주입**: `*_dialog.py`가 출력하는 `DELIBERATION_CONTEXT` JSON을 심의 agent 프롬프트에 직접 포함

## 스킬 프레임워크 & OMC 적용

[`.claude/skills/`](.claude/skills/)에 정적 베스트프랙티스를 SKILL.md 표준으로 관리. 동적 빈도 데이터는 [heal_stats.json](state/heal_stats.json)에 기록되며, [06a_dialog.py](scripts/06a_dialog.py)가 Top 5 빈출 패턴을 DELIBERATION_CONTEXT에 자동 주입.

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
| 힐링 루프 (05_execute 실패 시) | `/oh-my-claudecode:ultraqa` | `heal-patterns`, `browser-qa` | 06_heal → 06_auto_heal → (잔여) 06a_dialog 순서 준수. 최대 3회, 동일 오류 2회 반복 시 자동 스킵. 패치마다 lessons_learned 기록 |
| 병렬 공통 심의 (02a_parallel_dialog 후) | Agent tool 직접 | `playwright-best-practices`, `python-testing` | parallel_plan.json 저장 후 subagent spawn |
| 패치 후 검증 | `/oh-my-claudecode:verify` | `verify` | 힐링 패치 직후 05_execute 증거 확인. 통과 전 완료 선언 금지 |
| 패턴 등록 (세션 종료 전) | `/oh-my-claudecode:skillify` | `skillify` | 반복 패턴 발견 시 heal-patterns 또는 lessons_learned에 등록 |
| 슬롭 정리 (전체 통과 후) | `/oh-my-claudecode:ai-slop-cleaner` | — | 힐링/병렬 완료 후 생성 코드 품질 정리. 동작 변경 없이 중복·죽은 코드 제거 |

## 힐링

힐링 완료 필수: (1) 코드 패치 (2) [lessons_learned.md](agents/lessons_learned.md)에 교훈 기록 (중복 시 생략, 자동 로그는 [_auto.md](agents/lessons_learned_auto.md)에 별도 기록) (3) 재실행 통과 확인.
lint 수정·코드 생성 시 반복 오류도 동일하게 lessons_learned.md에 즉시 기록.
오류 유형별 패치 전략 → [Heal Patterns SKILL.md](.claude/skills/heal-patterns/SKILL.md). MCP 시각 검증 → [HEALING_GUIDE](doc/HEALING_GUIDE.md)
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
6. `python scripts/04_approve.py` — QA 리드 승인 게이트. 종료코드 0: 승인 / 2: 반려→재작성 (config/pipeline.json의 auto_approve=true가 기본값이라 보통 즉시 승인됨; "대시보드 대기" 폴백은 UI가 없는 데드엔드라 #26에서 제거)
7. `python scripts/05_execute.py` — pytest 실행
8. `python scripts/06_heal.py` — 종료코드 0: 완료 / 10: 힐링→재실행 반복 / 2: 초과→수동 수정
9. `python scripts/06_auto_heal.py` — 결정적 패턴 자동 패치 (Agent 호출 전). 종료코드 0: 완료·재실행 / 1: 잔여 실패→10번으로 / 3: 스킵(heal_needed 아님)
10. (exit 1시) `python scripts/06a_dialog.py` → [심의] [heal_deliberation.md](prompts/heal_deliberation.md) + ctx
11. (exit 1시) Agent 패치 → `python scripts/assert_guard.py` 실행

> **실행 순서 근거**: 06_auto_heal은 결정적 패턴 매칭으로 쉬운 케이스를 먼저 제거한다.
> 06a_dialog(심의)는 자동 수정 후 **남은 어려운 실패만** 컨텍스트에 담으므로 Agent 지시가 더 정확해진다.

> **리포트/스크린샷/Trace 규칙 (필수)**:
> - **첫 실행 포함 모든 실행은 `--no-report`로 실행**. 리포트·스크린샷은 전체 통과 확인 후 마지막 1회만 생성.
> - 실행 순서: `05_execute.py --no-report` → `06_heal.py` → 패치 → `05_execute.py --no-report` → ... → 전체 통과 확인 → `05_execute.py` (리포트 생성)
> - **힐링 재실행 시**: `05_execute.py --no-report --only-failed`로 실패 테스트만 재실행 가능
> - 05_execute.py는 매 실행 전 `tests/screenshots/`, `tests/traces/` 초기화.
> - **Trace**: 실패한 TC에 한해 `tests/traces/{group}__{test}.zip` 자동 생성. 힐링 시 `meta.json`의 `trace_path` 참조. 뷰어: `npx playwright show-trace <파일>.zip`

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
7. 실패 시 단일과 동일한 힐링 플로우 ([HEALING_GUIDE](doc/HEALING_GUIDE.md) 참조). 최대 3회, 초과 시 수동 수정 요청
8. **슬롭 정리 (선택, 전체 통과 후)**: 여러 subagent가 생성한 파일의 스타일 불일치·중복 정리
   `/oh-my-claudecode:ai-slop-cleaner tests/generated/`

## 팀 토론

`python run_team.py --topic "주제"` → 사수/부사수 멀티라운드 토론 → 대시보드 승인/반려.
상세 → [TEAM_DISCUSSION](doc/TEAM_DISCUSSION.md)

## 참조

- state/pipeline.json 스키마 → [PIPELINE_STATE](doc/PIPELINE_STATE.md)
- 디렉토리 구조 → [DIRECTORY](doc/DIRECTORY.md)
- 스크립트 인자/옵션 상세 → [SCRIPTS_GUIDE](doc/SCRIPTS_GUIDE.md)
- CLI 옵션 + API 엔드포인트 → [API_REFERENCE](doc/API_REFERENCE.md)
- 프롬프트 템플릿 입출력 → [PROMPTS_REFERENCE](doc/PROMPTS_REFERENCE.md)
