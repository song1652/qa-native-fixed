# 파이썬 파일 실행 가이드

> **독자**: 사람 — 모든 .py 파일의 역할과 실행 방법 정리. 에이전트가 읽지 않음.

---

## 한눈에 보기

```
직접 실행하는 파일 (진입점)
├── run_qa.py                  ← QA 자동화 시작 (단일 URL)
├── run_qa_parallel.py         ← QA 자동화 시작 (여러 URL 동시)
├── run_team.py                ← 팀 토론 시작 (터미널용, 대시보드 권장)
├── agents/dashboard/serve.py  ← 모니터링 대시보드 서버
├── parallel/99_merge.py       ← 병렬 실행 완료 후 결과 통합
└── _bootstrap.py              ← 루트 진입점 공통 경로 설정 (scripts/ → sys.path)

Claude가 자동으로 호출하는 파일 (직접 실행 불필요)
└── scripts/                       ← 패키지 (__init__.py 포함)
    ├── 01_analyze.py              파이프라인 1단계: DOM 분석
    ├── 02a_dialog.py              파이프라인 2단계: Plan 심의 준비
    ├── 02_generate.py             파이프라인 3단계: 코드 뼈대 생성
    ├── 03_lint.py                 파이프라인 4단계: lint 검사
    ├── 03a_dialog.py              파이프라인 5단계: 코드 리뷰 심의 준비
    ├── 05_execute.py              파이프라인 6단계: pytest 실행 (report_html 사용)
    ├── 06_heal.py                 파이프라인 7단계: 실패 분석
    ├── 06a_dialog.py              파이프라인 8단계: 힐링 심의 준비
    ├── team_discuss.py            팀 토론: 심의 컨텍스트 준비
    ├── team_approve.py            팀 토론: 결론 승인 (터미널용, 대시보드 권장)
    ├── check_pending_*.py         훅 5개 (hook_utils.check_state() 공통 사용)
    ├── coverage_matrix.py         커버리지 매트릭스 생성 (tc_*.md → state/coverage.json)
    ├── flaky_detector.py          Flaky Test 감지 (run_history.json → state/flaky_tests.json)
    ├── _python.py                 라이브러리: .venv Python 경로 (PROJECT_ROOT는 _paths.py에서 import)
    ├── _paths.py                  라이브러리: 중앙 경로 상수 + read_state/write_state
    ├── _constants.py              라이브러리: 종료 코드 + VALID_TRANSITIONS 전이 맵
    ├── result_parser.py           라이브러리: pytest JSON 리포트 파싱 (05_execute, 99_merge 공유)
    ├── hook_utils.py              라이브러리: 훅 스크립트 공통 유틸 (check_state)
    ├── __init__.py                패키지 초기화
    ├── sync_test_data.py          test_data.json 동기화
    ├── dom_helpers.js             JS 공통 유틸 (isVisible·esc·getSelectorsSimple) — 01_analyze.py의 _js()가 자동 주입
    └── parse_cases.py             라이브러리: 테스트케이스 파일 파서
```

---

## 직접 실행하는 파일

### `run_qa.py` — QA 자동화 시작 (단일 URL)

테스트할 URL과 케이스 폴더를 지정하면 headless Claude Code 세션을 백그라운드로 띄워 파이프라인 전체를 자동 완주합니다.

```bash
# 케이스 폴더 지정 (권장) — 폴더 내 tc_*.md 파일 전체를 자동 읽음
python run_qa.py --url https://example.com/ --cases testcases/mysite/

# 단일 파일 지정
python run_qa.py --url https://example.com/ --cases testcases/mysite/tc_01.md

# 자동 실행 없이 안내 메시지만 출력 (기존 방식)
python run_qa.py --url https://example.com/ --cases testcases/mysite/ --no-auto
```

**옵션:**
| 옵션 | 설명 |
|---|---|
| `--url` | 테스트 대상 URL (필수) |
| `--cases` | 케이스 파일 또는 폴더 경로 (필수) |
| `--no-auto` | headless Claude 자동 실행 생략. 안내 메시지만 출력 (기존 동작) |

**동작 순서 (`--auto` 기본):**
1. `testcases/` 폴더에서 케이스 파일 읽기
2. `state/pipeline.json` 생성 (URL + 케이스 목록)
3. `claude -p` headless 세션 백그라운드 실행 → `01_analyze → 코드작성 → lint → 승인 → 실행 → 힐링` 자동 완주
4. 로그: `logs/run_qa_headless.txt`

---

### `run_qa_parallel.py` — QA 자동화 시작 (여러 URL 동시)

`config/pages.json`에 등록된 URL을 기반으로 여러 URL을 동시에 테스트합니다.  
DOM 분석 후 headless Claude Code 세션을 백그라운드로 띄워 subagent 병렬 실행 + 99_merge + 힐링까지 자동 완주합니다.

```bash
# pages.json에 등록된 모든 URL 자동 스캔 (headless 자동 실행)
python run_qa_parallel.py

# 특정 폴더만
python run_qa_parallel.py --folders login saintcore

# targets.json 지정
python run_qa_parallel.py --targets testcases/targets_demo.json

# 자동 실행 없이 안내 메시지만 출력 (기존 방식)
python run_qa_parallel.py --no-auto
```

**옵션:**
| 옵션 | 설명 |
|---|---|
| `--targets` | targets.json 경로. 생략 시 `testcases/` 폴더 자동 스캔 |
| `--folders` | 특정 폴더만 실행 (예: `login saintcore`) |
| `--no-auto` | headless Claude 자동 실행 생략. `PARALLEL_SUBAGENT_CONTEXTS` 출력 + 안내 메시지만 출력 (기존 동작) |

**`config/pages.json` 형식 (string/object 혼용 가능):**
```json
{
  "mysite": "https://example.com/",
  "login": {
    "url": "https://example.com/login",
    "auth": null,
    "spa": true,
    "preconditions": [],
    "notes": "SPA 로그인 페이지"
  }
}
```
키 이름 = `testcases/` 하위 폴더명과 일치해야 합니다. 해당 폴더가 없는 키는 자동 건너뜁니다.
object 형식 사용 시 `page_meta`(auth, spa, preconditions, notes)가 subagent 컨텍스트에 자동 포함됩니다.

**동작 순서 (`--auto` 기본):**
1. `config/pages.json` 읽기 + `testcases/` 폴더 자동 스캔
2. URL별 DOM 분석 (동일 URL 1회만, 캐시)
3. `state/parallel_contexts.json` 저장 → 구조: `{ shared_context_paths: {...}, subagents: [...] }`
   - `shared_context_paths`: 공통 참조 파일 경로 (lessons_learned, team_charter, SKILL.md) — 각 subagent가 직접 읽음
   - `subagents[]`: 배치별 고유 데이터 (dom_info, test_cases, test_data 등)
4. `claude -p` headless 세션 백그라운드 실행 → `subagents[]` Agent tool 동시 실행 → `99_merge.py` → 힐링 자동 완주
5. 로그: `logs/run_qa_parallel_headless.txt`

---

### `parallel/99_merge.py` — 병렬 실행 결과 통합

모든 worker의 코드 생성이 완료된 후 실행합니다. Claude가 지시를 출력하면 그때 실행합니다.

```bash
python parallel/99_merge.py
# 특정 그룹만 실행
python parallel/99_merge.py --group mysite
# 빠른 실행 모드 (state/quick.json에 결과 저장, parallel_state 미변경)
python parallel/99_merge.py --quick --group mysite
# 힐링 생략 (실패해도 힐링 없이 바로 리포트 생성)
python parallel/99_merge.py --quick --group mysite --no-heal
```

**옵션:**
| 옵션 | 설명 |
|---|---|
| `--group`, `-g` | 실행할 폴더명 (예: `mysite`). 생략 시 전체 실행 |
| `--quick` | 빠른 실행 모드. 결과를 `state/quick.json`에 저장 (`state/parallel.json` 미변경) |
| `--no-heal` | 힐링 생략. 실패해도 `heal_context.json`을 생성하지 않고 바로 리포트 생성. 상태는 `done`으로 설정 |

**동작:**
1. `tests/generated/` 폴더 pytest 일괄 실행 (병렬 8 workers, timeout=900s)
2. **실패 시**: 단일 파이프라인과 동일한 힐링 플로우 실행 — 에러 분류(7종) → 사이트 사전 접근 체크 → 반복 실패 감지(2회 스킵) → `06_auto_heal.py` (deterministic 패치) → `state/heal_context.json` 생성 → Claude Code 패치 → 재실행 (최대 3회). `--no-heal` 시 이 단계를 건너뜀
3. 전체 통과 시: `tests/reports/parallel_index_{날짜시간}.html` 리포트 생성
4. `--group` 지정 시 리포트에 해당 그룹만 포함 (미선택 그룹 제외)

> 리포트는 같은 `group_dir`(폴더명)의 케이스를 하나의 그룹 카드로 묶어 표시합니다.

---

### `agents/dashboard/serve.py` — 모니터링 대시보드

사수/부사수 대화를 실시간으로 보고, 팀 토론을 진행·승인할 수 있는 웹 UI 서버입니다.

```bash
python agents/dashboard/serve.py
# 브라우저에서 http://localhost:8766 자동 열림
```

**대시보드에서 할 수 있는 것:**
| 기능 | 방법 |
|---|---|
| **단일 파이프라인 실행** | 단일 파이프라인 탭 → 페이지 선택 → URL 자동 표시 → 케이스 폴더 선택 → "run_qa.py 실행" 버튼 |
| **병렬 파이프라인 실행** | 병렬 파이프라인 탭 → "run_qa_parallel.py 실행" 버튼 (pages.json + testcases/ 자동 스캔) |
| **빠른 실행** | 빠른 실행 탭 → tests/generated/ 폴더 체크박스 선택 → "힐링 생략" 체크(선택) → "테스트 실행" 버튼 (전체 파이프라인 불필요) |
| **99_merge.py 실행** | 병렬 파이프라인 탭 → 워커 완료 후 "99_merge.py 실행" 버튼 |
| 단일 파이프라인 진행 상태 | 리뷰 완료 후 자동 실행 (승인 단계 없음) |
| 실행 로그 실시간 확인 | 실행 버튼 클릭 후 하단 로그 박스에 3초 간격 폴링 표시 |
| 파이프라인 진행 상태 모니터링 | 단일: 6단계 프로그레스 바 / 병렬: 워커 카드 그리드 |
| 테스트 결과 필터·페이지네이션 | All/Pass/Fail 필터 버튼 + 20개 단위 페이지 (단일·병렬·빠른 실행 공통) |
| **힐링 통계 시각화** | Overview 대시보드에 Heal Stats 위젯: 오류 유형별 도넛 차트 + Top 5 빈출 패턴 목록 |
| 팀 토론 실시간 모니터링 | 사수/부사수 티키타카 대화가 발언마다 실시간 표시 (SSE) |
| 팀 토론 시작 | 팀 토론 섹션 주제 입력 → 토론 시작 버튼 |
| 토론 결론 항목별 승인 | 각 항목 ✓/✗ 버튼 클릭 |
| 승인 후 자동 구현 | 전체 투표 완료 시 스케줄러(2분 내)가 자동으로 Claude에게 구현 지시 |
| 테스트 리포트 열람 | 리포트 목록 탭 → 리포트 클릭 (인라인 iframe 또는 새 탭) |
| 대화 초기화 | 우측 상단 "대화 초기화" 버튼 |

> **참고**: QA 파이프라인 심의(Plan·코드리뷰·힐링)는 대시보드에 표시되지 않습니다.
> 결과는 `state/pipeline.json`에 저장되며, 터미널 로그에서 확인할 수 있습니다.

**대시보드 API 엔드포인트:**
| 엔드포인트 | 메서드 | 설명 |
|---|---|---|
| `/api/run_qa` | POST | 단일 파이프라인 실행 (`url`, `cases_dir` 필요) |
| `/api/run_qa_parallel` | POST | 병렬 파이프라인 실행 |
| `/api/run_merge` | POST | 99_merge.py 실행 |
| `/api/run_quick` | POST | 빠른 실행 — 선택 그룹만 pytest 실행 (`groups` 배열 필요, `no_heal` 옵션) |
| `/api/run_log` | POST | 실행 로그 조회 (`log` 파일명 지정) |
| `/api/pipeline_state` | GET | 단일 파이프라인 state/pipeline.json 조회 |
| `/api/batch_state` | GET | 병렬 파이프라인 상태 조회 |
| `/api/quick_state` | GET | 빠른 실행 상태 조회 (`state/quick.json`) |
| `/api/generated_groups` | GET | tests/generated/ 하위 그룹별 파일 목록 조회 |
| `/api/pages` | GET | pages.json + testcases 그룹 목록 조회 |
| `/api/reports` | GET | 테스트 리포트 목록 조회 |

**서버 재시작 방법 (코드 변경 후):**
```bash
# 포트 확인 (macOS)
lsof -i :8766
# PID 종료
kill -9 [PID]
# 재시작
python agents/dashboard/serve.py
```

---

### `run_team.py` — 팀 토론 시작 (터미널용)

> **권장:** 대시보드의 "토론 시작" 버튼 사용. `run_team.py`는 대시보드 없이 터미널에서만 쓸 때 사용.

```bash
python run_team.py --topic "함수명 영문 번역 기준 정의"
python run_team.py  # 주제를 대화형으로 입력
```

**동작:** `state/discuss.json` 생성 후 다음 단계 안내 출력.
이후 Claude에게 직접 "팀 토론 진행해줘"라고 요청하면 됩니다.

---

## Claude가 자동으로 호출하는 파일 (scripts/)

> 아래 파일들은 **직접 실행하지 않습니다.** `run_qa.py` 실행 후 Claude가 순서대로 자동 호출합니다.
> 문제 해결 목적으로 개별 실행이 필요할 때만 참고하세요.

### 단일 파이프라인 순서

```
01_analyze.py
  → 메인 URL + 서브페이지 DOM을 단일 브라우저에서 분석 (메인: networkidle+30s, 서브: load+500ms, Semaphore(8))
  → 9가지 다중 셀렉터 전략 (id > testid > aria-label > role > placeholder > name > text > css > xpath) 추출
  → inputs/buttons: visible + hidden 모두 포함 (visible 플래그 구분)
  → navItems: 사이드바·메뉴 li 항목 추출 (nav li, aside li, [role="treeitem"] 등 최대 50개)
  → hidden_elements: 모달·드롭다운 컨테이너 + 내부 자식 버튼·링크 텍스트
  → testidElements: data-testid/data-test/data-cy/data-qa 속성명과 값을 실제 속성명 기준으로 추출
  → analyze_dynamic(): hover·click 트리거 순회 → 노출 요소 캡처 (30초 상한, 페이지 복원 실패 시 중단)
  → analyze_contextmenu(): 우클릭 후보 순회 → 컨텍스트 메뉴 캡처 (30초 상한, 중복 시그니처 제거)
  → 정적 DOM TTL 7일 / 동적 요소 TTL 24시간 분리 관리 (만료 시 동적 분석만 재실행)
  → --force-refresh 플래그: 캐시를 무시하고 강제 재분석
  → --skip-dynamic 플래그: 동적 UI 분석 건너뜀 (정적 DOM만 추출)

02a_dialog.py
  → Plan 심의에 필요한 파일들을 병렬로 읽어 JSON으로 출력
  → Claude가 이 출력을 보고 사수/부사수 심의 진행

02_generate.py
  → plan 기반으로 tests/generated/{group}/ 디렉토리에 케이스별 scaffold 파일 생성
  → Claude가 각 scaffold를 완성 코드로 채움 (tc_*.md 1개 = 테스트 파일 1개)

03_lint.py
  → flake8으로 생성된 테스트 코드 품질 검사
  → state/pipeline.json에 lint_result 저장, step=reviewed 설정
  → 이후 check_pending_approve.py 훅이 step=reviewed를 감지하여 05_execute.py 트리거

03a_dialog.py
  → 코드 리뷰 심의에 필요한 파일들을 병렬로 읽어 JSON으로 출력
  → Claude가 lint 결과 + 코드를 보고 리뷰 진행

05_execute.py
  → pytest로 테스트 실행 (최대 8 workers 병렬)
  → report_html.build_report()로 HTML 리포트 생성 (병렬과 동일 형식)
  → result_parser.parse_results()로 결과 파싱 (99_merge.py와 공유)
  → state/pipeline.json에 execution_result 저장 (heal_count는 읽기만, 증가 안 함)
  → `--no-report` 플래그: 리포트·스크린샷 생성 건너뜀 (힐링 중간 실행용)
  → `--only-failed` 플래그: 이전 실행에서 실패한 테스트만 재실행 (힐링 시 시간 대폭 절감)
  → 첫 실행 포함 모든 실행은 `--no-report`, 전체 통과 확인 후 마지막 1회만 리포트 생성
  → 매 실행 전 `tests/screenshots/`, `tests/traces/` 초기화
  → 워커 자동 감소 재실행 (8→4→2→1):
    처음엔 최대 8워커로 실행. 실패율 15% 이상이면 워커를 절반으로 줄여 실패분만 자동 재실행.
    각 단계 결과를 원래 결과에 병합하여 최종 리포트에 반영.
    (외부 사이트 rate limiting / 병렬 타이밍 이슈 자동 대응)

06_heal.py
  → 05_execute가 생성한 JSON 리포트(json_report_path)에서 실패 정보를 파싱 (pytest 재실행 없음)
  → 스크린샷·Trace 경로를 연결해 heal_context 저장 (meta.json의 trace_path 참조). 타임아웃 600s, -n8 병렬
  → --lf 실행 시 0개 수집이면 --lf 없이 재실행 (fallback)

06_auto_heal.py
  → 06_heal.py 이후 자동 패치. 8개 정적 패턴:
     strict mode violation → .first 추가
     timeout 오류 → timeout 값 증가 (5000→15000, 10000→20000)
     to_have_class(r"...") → to_have_class(re.compile(r"..."))
     triple_click() → click(click_count=3)
     page.evaluate('return ...') → page.evaluate('() => ...')
     UnicodeDecodeError cp949 → open() 에 encoding='utf-8' 추가
     모달 wait_for timeout 10000 → 20000
     광고 간섭 → adsbygoogle 제거 코드 삽입
  + heal_stats 빈출 패턴 Top 5 보고
  → 수정 파일만 재실행하여 검증. 전부 통과 시 Agent 불필요 (종료코드 0)
  → 잔여 실패 시 heal_context 업데이트 후 Agent에 위임 (종료코드 1)

06a_dialog.py
  → 힐링 심의에 필요한 파일들을 병렬로 읽어 JSON으로 출력
  → heal_stats.json에서 Top 5 빈출 패턴을 DELIBERATION_CONTEXT에 자동 주입
  → Claude가 traceback + 스크린샷 + 빈출 패턴을 분석해 코드 패치 후 05_execute.py 재실행
```

**개별 실행이 필요한 경우 (cwd = 프로젝트 루트):**
```bash
python scripts/01_analyze.py
python scripts/03_lint.py
python scripts/05_execute.py
# 등...
```

---

### 팀 토론 관련

| 파일 | 역할 | 실행 주체 |
|---|---|---|
| `scripts/team_discuss.py` | 토론 컨텍스트 준비 + dialog.json 세션 생성 | 대시보드 버튼 클릭 시 자동 실행 |
| `scripts/team_approve.py` | 결론 표시 후 y/n 승인 (터미널용) | 대시보드 승인 버튼으로 대체됨 |

---

### 훅 스크립트 (UserPromptSubmit Hook)

> `.claude/settings.json`에 등록되어 사용자 프롬프트 제출 시 자동 실행됩니다.
> 모든 훅은 `hook_utils.check_state(path, key, value, extra_check)` 공통 함수를 사용합니다.

| 파일 | 감지 대상 | 동작 |
|---|---|---|
| `scripts/check_pending_approve.py` | `state/pipeline.json`의 리뷰 완료 상태 | Claude에게 테스트 실행 지시 |
| `scripts/check_pending_discuss.py` | `state/discuss.json`의 토론 요청 | Claude에게 팀 토론 진행 지시 |
| `scripts/check_pending_impl.py` | `pending_impl.json` 존재 여부 | Claude에게 승인 항목 자동 구현 지시 |
| `scripts/check_pending_parallel.py` | `state/parallel.json`의 `status=ready` | Claude에게 병렬 subagent 실행 지시 |
| `scripts/check_pending_pipeline.py` | `state/pipeline.json`의 실행 대기 상태 | Claude에게 단일 파이프라인 실행 지시 |
| `scripts/check_pending_quick_heal.py` | `state/quick.json`의 `status=heal_needed` | 빠른 실행 실패 시 HEAL_SUBAGENT_CONTEXTS 주입해 힐링 자동 시작 |

---

### 라이브러리 파일

| 파일 | 역할 | 직접 실행 |
|---|---|---|
| `scripts/_python.py` | `PROJECT_ROOT`를 `_paths.py`에서 import하여 `.venv` 경로 구성. `PYTHON_EXE` 상수 제공 | ❌ (다른 스크립트가 import) |
| `scripts/_paths.py` | 중앙 경로 상수 (`STATE_DIR`, `LOGS_DIR`, `DOM_CACHE_DIR`, `RUN_HISTORY` 등) + `DOM_CACHE_TTL_HOURS=168`(7일) / `DOM_DYNAMIC_CACHE_TTL_HOURS=24`(24시간) TTL 상수 + `read_state()` (락 파일 기반 크로스플랫폼 잠금) / `write_state()` (atomic rename + **pipeline.json FSM 전이 자동 검증**) / `append_run_history()` (락 파일로 read-modify-write 보호, Windows 포함 크로스플랫폼) / `get_cached_dom()` (정적·동적 TTL 분리 체크 — 동적 만료 시 `dynamic_elements`/`contextmenu_elements`만 제거) / `save_dom_cache()` (atomic write + `_cached_at` / `_dynamic_cached_at` 분리 저장) / `resolve_sub_doms(state)` (sub_dom_keys → {url:dom} 매핑) 유틸 | ❌ (다른 스크립트가 import) |
| `scripts/_constants.py` | 파이프라인 종료 코드 상수 (`EXIT_SUCCESS=0`, `EXIT_HEAL_NEEDED=10`, `EXIT_HEAL_EXCEEDED=2`, `EXIT_REJECTED=2`) + `VALID_TRANSITIONS` step 전이 맵 + `assert_valid_transition()` 검증 함수 | ❌ (다른 스크립트가 import) |
| `scripts/result_parser.py` | pytest JSON 리포트 → `{nodeid: passed}` 매핑 파싱. `05_execute.py`와 `99_merge.py`가 공유 | ❌ (다른 스크립트가 import) |
| `scripts/hook_utils.py` | 훅 스크립트 공통 유틸. `check_state(path, key, value, extra_check)` — 5개 `check_pending_*.py`가 공유 | ❌ (다른 스크립트가 import) |
| `scripts/structured_log.py` | 구조화된 로그 (JSON Lines). `slog(event, **kwargs)` → `logs/structured.jsonl`에 기록. 05_execute, 06_heal, 99_merge에서 사용. 파이프라인 병목 분석·이벤트 추적용 | ❌ (다른 스크립트가 import) |
| `scripts/heal_utils.py` (힐링 배치 병렬화: `build_heal_batches()` + `print_heal_batches()` — 단일/병렬/빠른 공통, HEAL_BATCH_SIZE=6) | 힐링 공용 유틸리티. `classify_error` (7분류: Locator/Assertion/Timeout/URL/JS평가/Python런타임/Playwright일반/기타), `MCP_SNAPSHOT_ERROR_TYPES`, `extract_key_lines`, `find_screenshot_for_test`, `append_lessons` (→ `lessons_learned_auto.md`에 자동 기록), `update_heal_stats` — `06_heal.py`와 `99_merge.py`에서 공유 | ❌ (다른 스크립트가 import) |
| `scripts/parse_cases.py` | `.md`/`.json` 테스트케이스 파일 파서 (YAML frontmatter 지원) | ❌ (run_qa.py가 import해서 사용) |
| `tests/test_core_parsers.py` | 핵심 파서 유닛 테스트 (parse_cases 등) | ❌ (pytest가 자동 실행) |
| `scripts/sync_test_data.py` | `test_data.json` 동기화 유틸 | ❌ (필요 시 import) |
| `tests/conftest.py` | pytest browser/page fixture + 실패 시 스크린샷 자동 캡처 | ❌ (pytest가 자동 로드) |

---

## OMC 스킬 활용 (oh-my-claudecode)

> 상세 명령·참조 SKILL.md·적용 방법은 `CLAUDE.md` "스킬 프레임워크 & OMC 적용" 섹션 참조.

| 단계 | 명령 |
|------|------|
| 코드 완성 | `/oh-my-claudecode:ultrapilot` |
| 린트 수정 | Agent tool 직접 병렬 호출 |
| 힐링 루프 | `/oh-my-claudecode:ultraqa` |

---

## 설정 파일 (config/)

| 파일 | 역할 | 예시 키 |
|---|---|---|
| `config/pages.json` | 페이지명 → URL 매핑. `run_qa_parallel.py`가 자동 참조 | `"mysite": "https://example.com/"` |
| `config/test_data.json` | 테스트 입력값 중앙 관리. 테스트 코드에서 하드코딩 금지, 이 파일에서 읽어 사용 | `"mysite": { "valid_user": {...}, ... }` |

`test_data.json` 형식: `{ "페이지명": { "data_key": { "username": "...", "password": "..." } } }`
- 키는 `pages.json`의 페이지명과 일치
- 테스트케이스 frontmatter의 `data_key`가 이 파일의 서브키를 참조
- 실제 내용은 `config/test_data.json` 직접 참조

---

## 상태 파일 (실행 결과가 저장되는 곳)

| 파일 | 저장 내용 | 생성 시점 |
|---|---|---|
| `state/pipeline.json` | 단일 파이프라인 전체 상태 (dom_info, plan, review_summary, heal_context 등) | `run_qa.py` 실행 시 |
| `state/discuss.json` | 팀 토론 상태 (주제, 결론, 투표 항목) | 대시보드 토론 시작 시 |
| `agents/dialog.json` | **팀 자유 토론 대화 로그 전용** (QA 파이프라인 심의는 기록 안 함) | 팀 토론 시작 시 |
| [`agents/team_notes.md`](../agents/team_notes.md) | 승인된 팀 결정사항 (구현 완료 후 초기화) | 토론 항목 전체 투표 완료 시 |
| [`agents/lessons_learned.md`](../agents/lessons_learned.md) | 큐레이션된 실수 패턴 (수동 관리) | 힐링·코드리뷰 심의 완료 시 |
| [`agents/lessons_learned_auto.md`](../agents/lessons_learned_auto.md) | 자동 기록 힐링 로그 (heal_utils.py) | 06_heal.py 실행 시 자동 |
| `pending_impl.json` | 승인 후 구현 대기 항목 (훅이 감지해 자동 구현) | 대시보드 전체 투표 완료 시 |
| `state/parallel.json` | 병렬 파이프라인 실행 결과 (targets, 통계) | `99_merge.py` 완료 시 |
| `state/quick.json` | 빠른 실행 결과 (병렬 상태와 분리) | `99_merge.py --quick` 완료 시 |
| `state/heal_context.json` | 병렬 파이프라인 힐링 컨텍스트 (에러 분류, failure_groups, skipped_repeated, lessons_snapshot 포함) | `99_merge.py` 실패 시 |
| `state/heal_stats.json` | 힐링 오류 패턴별 빈도 카운터 (Top 5를 심의 컨텍스트에 주입) | `06_heal.py` 실패 분석 시 |
| `state/run_history.json` | 실행 이력 배열 (timestamp, passed/failed, heal_count, first_pass, duration_sec) | 매 실행 완료 시 자동 append |
| `logs/merge.txt` | 99_merge.py 실행 로그 | `99_merge.py` 실행 시 |
| `logs/quick_run.txt` | 빠른 실행 로그 | 대시보드 빠른 실행 시 |
| `logs/run_parallel.txt` | 병렬 파이프라인 실행 로그 | 대시보드에서 병렬 실행 시 |
| `logs/run_qa.txt` | 단일 파이프라인 실행 로그 | 대시보드에서 단일 실행 시 |
| `logs/run_qa_headless.txt` | `run_qa.py` headless 세션 전체 로그 | `run_qa.py` (--auto) 실행 시 |
| `logs/run_qa_parallel_headless.txt` | `run_qa_parallel.py` headless 세션 전체 로그 | `run_qa_parallel.py` (--auto) 실행 시 |
| `state/parallel_contexts.json` | 병렬 파이프라인 subagent 컨텍스트 전체 (dom_info + test_cases + shared_paths) | `run_qa_parallel.py` 실행 시 |
