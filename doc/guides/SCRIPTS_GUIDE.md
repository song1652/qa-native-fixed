# 파이썬 파일 실행 가이드

> **문서 유형: 사용 매뉴얼** · 프로젝트 실행 방법과 주요 스크립트 역할. 정확한 인자·API는 [API 레퍼런스](../reference/API_REFERENCE.md)를 참고합니다.

> **독자**: 프로젝트 사용자·개발자 — 주요 Python 파일의 역할과 실행 방법.

---

## 처음 실행하는 사람을 위한 순서

### 1. 실행할 터미널과 위치 확인

이 문서의 모든 명령은 **프로젝트 루트**, 즉 `run_qa.py`와 `requirements.txt`가 있는 폴더에서 실행합니다. 웹에서만 작업하려면 [대시보드 가이드](DASHBOARD_USER_GUIDE.md)를 먼저 읽어도 됩니다.

```sh
pwd
python3 --version
claude --version
```

`pwd`가 다른 폴더라면 프로젝트 폴더로 이동합니다. `claude` 명령을 찾지 못하면 [설치 안내](../../README.md#설치)를 따라 CLI를 준비하고 로그인합니다. TC 생성과 코드 생성은 서버가 실행되는 PC의 Claude CLI를 사용합니다.

이 문서의 `.venv/bin/python`은 프로젝트 가상환경의 Python입니다. 해당 파일이 없다면 설치 안내에 따라 환경을 준비하거나 의존성을 설치한 Python 실행 경로로 바꿉니다.

### 2. 어떤 명령을 사용할지 선택

| 목적 | 명령 또는 화면 | 실행 전에 준비할 것 |
|---|---|---|
| 웹 대시보드 열기 | `agents/dashboard/serve.py` | Python 의존성 |
| URL 하나의 TC로 코드 생성·실행 | `run_qa.py` | 실제 URL, Markdown TC 파일·폴더, Claude 로그인 |
| 여러 그룹 생성·실행 | `run_qa_parallel.py` | 페이지 URL 매핑, 그룹별 Markdown, Claude 로그인 |
| 생성된 코드를 다시 실행 | 대시보드의 빠른 실행 | `tests/generated/`의 코드 |
| 사용자 가이드만 읽기 | HTML 가이드 파일 또는 문서 서버 | 가이드·이미지 파일 |

QA 대시보드는 기본 **8766**, 문서 보기용 서버 예제는 **8768**입니다. 문서 서버를 켜는 것만으로 TC 생성이나 파이프라인 API가 동작하지는 않습니다.

### 3. 첫 실행은 한 그룹으로 확인

1. TC 스튜디오에서 검토한 Markdown을 반영하거나 [TC 작성 가이드](TEST_CASE_GUIDE.md)에 따라 한 그룹의 파일을 준비합니다.
2. 대상 URL을 브라우저에서 열어 TC가 설명하는 화면인지 확인합니다.
3. 계정·입력값이 필요한 케이스라면 해당 테스트 데이터도 준비합니다.
4. 아래의 단일 파이프라인 설명에 따라 실제 URL과 케이스 경로를 지정합니다.
5. 시작 안내가 나오면 로그와 대시보드에서 진행 상황을 확인합니다.
6. 완료 결과의 전체·통과·실패·건너뜀을 확인한 뒤 범위를 넓힙니다.

명령 예제의 `https://example.com/`과 `testcases/mysite/`는 자리 표시자입니다. 그대로 복사해도 사용자의 사이트와 케이스가 자동으로 선택되지는 않습니다.

### 4. 실행 명령이 끝났다는 뜻

진입점은 Claude 작업을 백그라운드로 시작할 수 있습니다. 따라서 터미널에 입력 프롬프트가 다시 나타났다는 이유만으로 테스트 완료라고 판단하지 않습니다. 안내된 로그와 대시보드 결과의 시각·완료 상태를 확인합니다.

`--no-auto`는 **초기 작업과 안내 후 Claude 자동 실행을 생략**하는 옵션입니다. 파이프라인 전체를 자동 완료하려는 초보자는 기본 실행을 사용합니다. 이름이 `--no-auto`라고 해서 상태를 전혀 바꾸지 않는 미리보기 명령으로 생각하지 마세요.

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
    ├── 04_approve.py              승인 게이트 (auto_approve 기본 → 즉시 승인)
    ├── 05_execute.py              파이프라인 6단계: pytest 실행 (report_html 사용)
    ├── 06_heal.py                 파이프라인 7단계: 실패 분석
    ├── 06_auto_heal.py            힐링: 결정적 패턴 자동 패치 (Agent 호출 전)
    ├── 06a_dialog.py              파이프라인 8단계: 힐링 심의 준비
    ├── report_html.py             라이브러리: HTML 리포트 생성 (05_execute, 99_merge 공유)
    ├── team_discuss.py            팀 토론: 심의 컨텍스트 준비
    ├── team_approve.py            팀 토론: 결론 승인 (터미널용, 대시보드 권장)
    ├── check_pending_*.py         훅 6개 (hook_utils.check_state() 공통 사용)
    ├── coverage_matrix.py         커버리지 매트릭스 생성 (tc_*.md → state/coverage.json)
    ├── flaky_detector.py          Flaky Test 감지 (run_history.json → state/flaky_tests.json)
    ├── _python.py                 라이브러리: .venv Python 경로
    ├── _paths.py                  라이브러리: 중앙 경로 상수 + read_state/write_state/update_state
    ├── _constants.py              라이브러리: 종료 코드 + VALID_TRANSITIONS 전이 맵
    ├── _pipeline_registry.py      라이브러리: FSM 단일 소스 (Step·ParallelStatus 상수 + 전이 규칙)
    ├── _validators.py             라이브러리: 대시보드 입력 검증 헬퍼 (serve.py에서 분리)
    ├── assert_guard.py            힐링 후 assertion 약화 감지
    ├── jira_reporter.py           Jira 이슈 자동 생성 (실패 시 99_merge.py가 자동 호출)
    ├── result_parser.py           라이브러리: pytest JSON 리포트 파싱 (05_execute, 99_merge 공유)
    ├── hook_utils.py              라이브러리: 훅 스크립트 공통 유틸 (check_state + remaining_steps_hint)
    ├── __init__.py                패키지 초기화
    ├── sync_test_data.py          test_data/{프로덕트}.json 동기화
    ├── build_user_guides.py       문서: guides/*.md → HTML 가이드 생성 (--check)
    ├── update_directory.py        문서: doc/reference/DIRECTORY.md 재생성
    ├── dom_helpers.js             JS 공통 유틸 (isVisible·esc·getSelectorsSimple) — 01_analyze.py의 _js()가 자동 주입
    └── parse_cases.py             라이브러리: 테스트케이스 파일 파서
```

---

## 직접 실행하는 파일

### `run_qa.py` — QA 자동화 시작 (단일 URL)

테스트할 URL과 케이스 폴더를 지정하면 headless Claude Code 세션을 백그라운드로 띄워 파이프라인 전체를 자동 완주합니다.

```bash
# 케이스 폴더 지정 (권장) — 폴더 내 tc_*.md 파일 전체를 자동 읽음
.venv/bin/python run_qa.py --url https://example.com/ --cases testcases/mysite/

# 단일 파일 지정
.venv/bin/python run_qa.py --url https://example.com/ --cases testcases/mysite/tc_01.md

# 자동 실행 없이 안내 메시지만 출력 (기존 방식)
.venv/bin/python run_qa.py --url https://example.com/ --cases testcases/mysite/ --no-auto
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
.venv/bin/python run_qa_parallel.py

# 특정 폴더만
.venv/bin/python run_qa_parallel.py --folders login saintcore

# targets.json 지정
.venv/bin/python run_qa_parallel.py --targets testcases/targets_demo.json

# 자동 실행 없이 안내 메시지만 출력 (기존 방식)
.venv/bin/python run_qa_parallel.py --no-auto
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

### `parallel/02a_parallel_dialog.py` — 병렬 공통 심의 컨텍스트

`run_qa_parallel.py` 다음, subagent 실행 전에 Claude가 호출합니다. `state/parallel_contexts.json`을 읽어 `DELIBERATION_CONTEXT_START ~ END` JSON을 출력합니다. Claude는 이를 보고 전체 그룹 공통 전략을 `state/parallel_plan.json`에 저장하고, 각 subagent는 `shared_context_paths.parallel_plan`으로 읽습니다. 옵션은 없습니다.

```bash
.venv/bin/python parallel/02a_parallel_dialog.py
```

### `parallel/99_merge.py` — 병렬 실행 결과 통합

모든 worker의 코드 생성이 완료된 후 실행합니다. Claude가 지시를 출력하면 그때 실행합니다.

```bash
.venv/bin/python parallel/99_merge.py
# 특정 그룹만 실행
.venv/bin/python parallel/99_merge.py --group mysite
# 빠른 실행 모드 (state/quick.json에 결과 저장, parallel_state 미변경)
.venv/bin/python parallel/99_merge.py --quick --group mysite
# 힐링 생략 (실패해도 힐링 없이 바로 리포트 생성)
.venv/bin/python parallel/99_merge.py --quick --group mysite --no-heal
```

**옵션:**
| 옵션 | 설명 |
|---|---|
| `--group`, `-g` | 실행할 폴더명 (예: `mysite`). 생략 시 전체 실행 |
| `--quick` | 빠른 실행 모드. 결과를 `state/quick.json`에 저장 (`state/parallel.json` 미변경) |
| `--no-heal` | 힐링 생략. 실패해도 `heal_context.json`을 생성하지 않고 리포트 생성. 실패 상태는 `heal_failed`로 보존 |
| `--no-report` | 리포트 생성 생략. 힐링 중 중간 실행 시 사용. Jira 이슈 생성도 건너뜀 |

**동작:**
1. `tests/generated/` 폴더 pytest 일괄 실행 (병렬 최대 4 workers, timeout=7200s). `rerunfailures` 비활성화
2. **실패 시**: setup·call·teardown·수집 오류와 pytest 종료코드를 함께 판정. 정상 종료(0·1)의 모든 실패가 Locator 오류일 때 `heal_context.json` 생성 → 새 DOM 수집 → 자동 패치와 파일당 한 번 검증. 검증 실패면 원본 복원 후 추가 실행 중단. 검증 실패 없이 미수정 후보가 남았을 때만 Agent 심의 가능. `--no-heal`은 복구를 생략
3. 전체 통과 시: `tests/reports/parallel_index_{날짜시간}.html` 리포트 생성
4. `--group` 지정 시 리포트에 해당 그룹만 포함 (미선택 그룹 제외)

> 리포트는 같은 `group_dir`(폴더명)의 케이스를 하나의 그룹 카드로 묶어 표시합니다.

---

### `agents/dashboard/serve.py` — 모니터링 대시보드

TC 작성·내보내기, 파이프라인 실행·모니터링, 리포트 열람과 팀 토론을 지원하는 웹 UI 서버입니다.

최신 밝은 테마 화면과 메뉴별 사용 방법은 [웹 QA 대시보드 사용자 가이드](DASHBOARD_USER_GUIDE.md)를 참고하세요. TC 작성부터 내보내기까지는 [TC 스튜디오 사용자 설명서](tc-studio/TC_AUTHORING_USER_GUIDE.md)에 있습니다.

```bash
.venv/bin/python agents/dashboard/serve.py
# 브라우저에서 http://localhost:8766 자동 열림

# 다른 인터페이스/포트로 실행
.venv/bin/python agents/dashboard/serve.py --host 0.0.0.0 --port 8800
```

| 옵션/환경 변수 | 기본값 | 설명 |
|---|---|---|
| `--host` | `127.0.0.1` | 서버 바인딩 주소 |
| `--port` | `8766` | 서버 바인딩 포트 |
| `ALLOWED_HOSTS` | `localhost:8766 127.0.0.1:8766` | 허용 `Host` 값. 쉼표 또는 공백 구분 |
| `ALLOWED_ORIGIN` | `http://localhost:8766` | 허용 브라우저 origin |
| `REMOTE_MODE` | 비활성 | 활성화 시 실행/reset API를 기본 403 차단 |
| `REMOTE_API_ALLOWLIST` | 빈 값 | 예외 허용 경로. exact match 또는 끝 `*` prefix match, 쉼표 구분 |

원격 모드는 인증 기능이 아닙니다. 외부 네트워크에 바인딩할 때는 허용 host/origin을
명시하고 인증 프록시를 별도로 구성하세요. 토론 결론의 승인/반려 API는 게이트 진행을
막지 않도록 원격 모드에서도 허용됩니다. 상세 위험 엔드포인트와 allowlist 규칙은
[`API_REFERENCE.md`](../reference/API_REFERENCE.md)를 참고하세요.

> **동적 포트(P0-3):** 현재 저장소에는 dashboard job 동시 실행 상한과 workspace
> 수명주기 계약이 없습니다. `--port`로 명시적 포트를 선택할 수 있지만, job별 자동
> 할당/해제는 해당 결정이 생길 때까지 보류합니다.

**대시보드에서 할 수 있는 것:**
| 기능 | 방법 |
|---|---|
| **단일 파이프라인 실행** | 단일 파이프라인 탭 → 페이지 선택 → URL 자동 표시 → 케이스 폴더 선택 → "파이프라인 실행" 버튼 |
| **병렬 파이프라인 실행** | 병렬 파이프라인 탭 → "병렬 실행" 버튼 (pages.json + testcases/ 자동 스캔) |
| **빠른 실행** | 빠른 실행 탭 → tests/generated/ 폴더 체크박스 선택 → "힐링 생략" 체크(선택) → "테스트 실행" 버튼 (전체 파이프라인 불필요) |
| **병렬 결과 병합** | 병렬 실행 흐름에서 처리. 수동 실행은 `python3 parallel/99_merge.py` 사용 |
| 단일 파이프라인 진행 상태 | 리뷰 완료 후 자동 실행 (승인 단계 없음) |
| 실행 로그 실시간 확인 | 실행 버튼 클릭 후 하단 로그 박스에 3초 간격 폴링 표시 |
| 파이프라인 진행 상태 모니터링 | 단일: 6단계 프로그레스 바 / 병렬: 워커 카드 그리드 |
| 테스트 결과 필터·페이지네이션 | 전체/통과/실패/건너뜀 필터 버튼 + 20개 단위 페이지 (단일·병렬·빠른 실행 공통) |
| **힐링 통계 시각화** | 대시보드의 힐링 통계: 오류 유형별 도넛 차트 + Top 5 빈출 패턴 목록 |
| 팀 토론 실시간 모니터링 | 사수/부사수 티키타카 대화가 발언마다 실시간 표시 (SSE) |
| 팀 토론 시작 | 팀 토론 섹션 주제 입력 → 토론 시작 버튼 |
| 토론 결론 항목별 승인 | 각 항목 ✓/✗ 버튼 클릭 |
| 승인 후 자동 구현 | 전체 투표 완료 시 스케줄러(2분 내)가 자동으로 Claude에게 구현 지시 |
| 테스트 리포트 열람 | 리포트 목록 탭 → 리포트 클릭 (인라인 iframe 또는 새 탭) |
| **TC 작성·내보내기** | TC 스튜디오 → 기획 정보 · 생성/라이브러리/초안 검토/내보내기 |

> **참고**: QA 파이프라인 심의(Plan·코드리뷰·힐링)는 대시보드에 표시되지 않습니다.
> 결과는 `state/pipeline.json`에 저장되며, 터미널 로그에서 확인할 수 있습니다.

**대시보드 API:** 전체 목록과 요청·응답 계약은 [API 레퍼런스](../reference/API_REFERENCE.md)를 참고하세요.

**서버 재시작 방법 (코드 변경 후):**
```bash
# 포트 확인 (macOS)
lsof -i :8766
# PID 종료
kill -9 [PID]
# 재시작
.venv/bin/python agents/dashboard/serve.py
```

---

### `run_team.py` — 팀 토론 시작 (터미널용)

> **권장:** 대시보드의 "토론 시작" 버튼 사용. `run_team.py`는 대시보드 없이 터미널에서만 쓸 때 사용.

```bash
.venv/bin/python run_team.py --topic "함수명 영문 번역 기준 정의"
.venv/bin/python run_team.py  # 주제를 대화형으로 입력
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
  → Claude가 이 출력을 보고 체크리스트로 plan을 작성

02_generate.py
  → plan 기반으로 tests/generated/{group}/ 디렉토리에 케이스별 scaffold 파일 생성
  → Claude가 각 scaffold를 완성 코드로 채움 (tc_*.md 1개 = 테스트 파일 1개)

03_lint.py
  → flake8으로 생성된 테스트 코드 품질 검사
  → state/pipeline.json에 lint_result 저장, step=reviewed 설정
  → 이후 check_pending_approve.py 훅이 step=reviewed를 감지하여 05_execute.py 트리거

03a_dialog.py
  → 코드 리뷰 심의에 필요한 파일들을 병렬로 읽어 JSON으로 출력
  → Claude가 lint 결과 + 코드를 체크리스트로 리뷰

04_approve.py
  → QA 리드 승인 게이트. review_summary 출력 후 y/n
  → config/pipeline.json의 auto_approve=true(기본) 또는 `--yes`면 즉시 승인
  → 종료코드 0: 승인 / 4: 반려(재작성) / 1: stdin 없음(비대화형인데 auto_approve 꺼짐) / 2: 3회 반려 초과

05_execute.py
  → pytest 실행 (최대 4 workers; spa: true 사이트는 순차 실행). rerunfailures 비활성화
  → 실행별 결과를 state/runs/{run_id}/execution_result.json에 원자적으로 저장
  → 최신 소유자일 때만 state/pipeline.json의 execution_result를 갱신
  → report_html.build_report()로 HTML 리포트 생성 (병렬과 동일 형식)
  → --no-report: HTML 생성 생략. 실패 스크린샷·Trace와 실행 결과는 저장
  → --only-failed: 안전한 수정 확인용으로 이전 실패만 선택. 중단된 복구에는 사용 금지
  → --state-path: worker 상태 경로. 모든 단계에 같은 경로 전달
  → JSON 리포트는 실행/호출별 경로, 증거 파일은 run_id__invocation_id__ 접두어로 분리
  → 기존 screenshots/traces/videos 폴더 전체를 초기화하지 않음

06_heal.py
  → 저장된 소유 JSON 리포트 또는 오류에서 모든 실패 단계·수집 오류를 읽음
  → 오류 수집을 위한 --lf·전체 pytest 재실행 없음
  → 모든 실패가 Locator이고 pytest 정상 종료(0·1)일 때만 복구 후보 준비
  → 현재 run_id·invocation_id에 속한 스크린샷·Trace만 연결
  → --state-path: worker 상태 경로
  → 종료코드 0: 실패 없음·대상 단계 아님 / 10: 후보 준비 / 2: 복구 불가·초과 등 중단

06_auto_heal.py
  → 소유 실행과 모든 실패의 복구 가능 여부를 재확인
  → 캐시를 무시하고 현재 URL의 새 DOM 수집. 클릭·호버 탐색은 생략
  → 새 DOM 수집 실패·빈 결과면 패치·검증 전에 종료코드 5로 중단
  → 7개 정적 패치 함수가 있으나 Locator 복구 허용 판정을 통과한 경우만 적용
  → 변경 파일당 검증 한 번: --maxfail=1 -p no:rerunfailures (파일별 timeout=300s)
  → 검증 실패·크래시·타임아웃·검증 중 종료 신호는 임시 파일 변경을 원래 바이트로 복원
  → 종료코드 0: 자동 검증 통과·잔여 없음 / 1: 검증 실패 없이 미수정 후보 남음
  → 종료코드 3: 스킵 / 5: 자동 복구 중단. exit 5·recovery_stopped 이후 추가 실행 금지
  → --state-path: 상태 파일 (기본 state/pipeline.json; 병렬 state/parallel.json)
  → --state-key: heal_needed 판정 키 (기본 step; 병렬 status)
  → --heal-context-path: 별도 컨텍스트 JSON (병렬 state/heal_context.json)
  → 검증 호출에도 별도 invocation_id와 증거 파일 접두어 부여

06a_dialog.py / assert_guard.py
  → --state-path: worker 상태 경로
  → 06a_dialog는 이미 중단된 복구에서 종료코드 5로 심의를 거부
  → 심의는 새 DOM·현재 실행의 오류/화면·빈출 패턴만 사용
  → assert_guard는 최초 또는 직전 assertion 스냅샷과 현재 파일을 비교
  → 기대값·assertion 약화로 실패를 숨기지 않음

```

**개별 실행이 필요한 경우 (cwd = 프로젝트 루트):**
```bash
.venv/bin/python scripts/01_analyze.py
.venv/bin/python scripts/03_lint.py
.venv/bin/python scripts/05_execute.py
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
> P44부터 트리거 조건 값은 `_pipeline_registry.py`의 `Step.*` / `ParallelStatus.*` 레지스트리 상수를 사용합니다.
> 실행 지시문은 `hook_utils.remaining_steps_hint(from_step)`이 레지스트리 기반으로 자동 생성합니다.
> `workflow_status`가 `failed`·`cancelled`·`interrupted`·`timed_out`·`incomplete`이면 `hook_utils.check_state()`가 잔존 단계의 실행 지시를 억제합니다. 새 실행은 진입점에서 시작합니다.

| 파일 | 감지 대상 | 트리거 상수 | 동작 |
|---|---|---|---|
| `scripts/check_pending_pipeline.py` | `state/pipeline.json` | `Step.INIT` | 단일 파이프라인 시작 지시 + 잔여 단계 목록 자동 출력 |
| `scripts/check_pending_approve.py` | `state/pipeline.json` | `Step.REVIEWED` | 테스트 실행 지시 + 잔여 단계 목록 자동 출력 |
| `scripts/check_pending_parallel.py` | `state/parallel.json` | `ParallelStatus.READY` | 병렬 subagent 실행 지시 + PARALLEL_SUBAGENT_CONTEXTS 주입 |
| `scripts/check_pending_quick_heal.py` | `state/quick.json` | `ParallelStatus.HEAL_NEEDED` | HEAL_SUBAGENT_CONTEXTS 주입해 힐링 자동 시작 |
| `scripts/check_pending_discuss.py` | `state/discuss.json` | `step="pending"` | Claude에게 팀 토론 진행 지시 |
| `scripts/check_pending_impl.py` | `pending_impl.json` | `status="pending"` | Claude에게 승인 항목 자동 구현 지시 |

---

### 라이브러리 파일

| 파일 | 역할 | 직접 실행 |
|---|---|---|
| `scripts/_python.py` | `PROJECT_ROOT`를 `_paths.py`에서 import하여 `.venv` 경로 구성. `PYTHON_EXE` 상수 제공 | ❌ (다른 스크립트가 import) |
| `scripts/_paths.py` | 중앙 경로 상수 (`STATE_DIR`, `LOGS_DIR`, `DOM_CACHE_DIR`, `RUN_HISTORY` 등) + `DOM_CACHE_TTL_HOURS=168`(7일) / `DOM_DYNAMIC_CACHE_TTL_HOURS=24`(24시간) TTL 상수 + `read_state()` (락 파일 기반 크로스플랫폼 잠금) / `write_state()` (atomic rename + **pipeline.json FSM 전이 자동 검증**) / `append_run_history()` (락 파일로 read-modify-write 보호, Windows 포함 크로스플랫폼) / `get_cached_dom()` (정적·동적 TTL 분리 체크 — 동적 만료 시 `dynamic_elements`/`contextmenu_elements`만 제거) / `save_dom_cache()` (atomic write + `_cached_at` / `_dynamic_cached_at` 분리 저장) / `resolve_sub_doms(state)` (sub_dom_keys → {url:dom} 매핑) 유틸 | ❌ (다른 스크립트가 import) |
| `scripts/_constants.py` | 파이프라인 종료 코드 상수 (`EXIT_SUCCESS=0`, `EXIT_HEAL_NEEDED=10`, `EXIT_HEAL_EXCEEDED=2`, `EXIT_REJECTED=4`) + `VALID_TRANSITIONS` step 전이 맵 + `assert_valid_transition()` 검증 함수 | ❌ (다른 스크립트가 import) |
| `scripts/error_policy.py` | 오류 분류·안내와 복구 허용 판정. 모든 실패 단계·수집 오류·pytest 종료 상태를 함께 확인하며 Locator 후보만 복구 허용 | ❌ (다른 스크립트가 import) |
| `scripts/run_results.py` | 실행 소유 결과의 원자적 읽기/쓰기, worker ID 파생. 취소·중단·시간 초과 결과를 뒤늦은 worker 결과로 덮어쓰지 않음 | ❌ (다른 스크립트가 import) |
| `scripts/result_parser.py` | pytest JSON 리포트 → `{nodeid: passed}` 매핑 파싱. `05_execute.py`와 `99_merge.py`가 공유 | ❌ (다른 스크립트가 import) |
| `scripts/hook_utils.py` | 훅 스크립트 공통 유틸. `check_state(path, key, value, extra_check)` + `remaining_steps_hint(from_step)` (레지스트리 기반 잔여 단계 지시문 자동 생성, P44) — 5개 `check_pending_*.py`가 공유 | ❌ (다른 스크립트가 import) |
| `scripts/structured_log.py` | 구조화된 로그 (JSON Lines). `slog(event, **kwargs)` → `logs/structured.jsonl`에 기록. 05_execute, 06_heal, 99_merge에서 사용. 파이프라인 병목 분석·이벤트 추적용 | ❌ (다른 스크립트가 import) |
| `scripts/heal_utils.py` (힐링 배치 병렬화: `build_heal_batches()` + `print_heal_batches()` — 단일/병렬/빠른 공통, HEAL_BATCH_SIZE=6) | 힐링 공용 유틸리티. 통계용 `classify_error` (Locator/Assertion/Timeout/URL/JS평가/Python런타임/Playwright일반/기타), 실행 소유권 확인·새 DOM 수집·소유 화면 조회, `MCP_SNAPSHOT_ERROR_TYPES`, `extract_key_lines`, `find_screenshot_for_test`, `append_lessons` (→ `lessons_learned_auto.md`에 자동 기록), `update_heal_stats` — `06_heal.py`와 `99_merge.py`에서 공유 | ❌ (다른 스크립트가 import) |
| `scripts/_pipeline_registry.py` | FSM 단일 소스. `Step.*` / `ParallelStatus.*` 상수, `PIPELINE_STEP_DEFS`(메타), `VALID_TRANSITIONS` / `VALID_PARALLEL_TRANSITIONS`, `make_initial_pipeline_state()` 팩토리 | ❌ (다른 스크립트가 import) |
| `scripts/_validators.py` | 대시보드 `serve.py` 입력 검증 헬퍼. `serve.py`의 백그라운드 스레드 부작용 없이 재사용 가능하도록 분리 | ❌ (serve.py + 테스트가 import) |
| `scripts/_tc_model.py` | TC 스튜디오 케이스 모델: 허용 값(P0~P3, 실행 결과), Step·Expected 파싱, 결과 병합, id 발급, 검증 규칙 | ❌ (다른 스크립트가 import) |
| `scripts/_tc_template.py` | 엑셀 TC 템플릿 분석: 헤더·하위 헤더·컬럼·드롭다운·No. 수식 탐지 → `TemplateProfile` | ❌ (다른 스크립트가 import) |
| `scripts/_tc_xlsx_import.py` | 엑셀 시트 → 라이브러리 케이스 (병합·빈 칸 이어받기, 기타 칸의 id·src 분리) | ❌ (다른 스크립트가 import) |
| `scripts/_tc_library.py` | TC 라이브러리 저장소 `state/tc_library/{suite}/`: rev 수정·일괄·생성·삭제·이력·트리·필터 | ❌ (대시보드가 import) |
| `scripts/_tc_xlsx_export.py` | 라이브러리 → 템플릿 사본 xlsx (병합·드롭다운·요약 수식·History) + 무결성 검사 | ❌ (대시보드가 import) |
| `scripts/_tc_sources.py` | TC 생성용 소스 묶음: 파일(PDF·DOCX·MD·TXT)·붙여넣기 → markdown 섹션 | ❌ (대시보드가 import) |
| `scripts/_tc_profiles.py` | TC 작성 프로필 저장소 + 기본 규칙 | ❌ (대시보드가 import) |
| `scripts/_tc_prompt.py` | TC 생성 프롬프트·출력 JSON 스키마·섹션 묶기 | ❌ (다른 스크립트가 import) |
| `scripts/_tc_review.py` | TC 초안 중복 후보·중복 처리·커버리지 갭 | ❌ (대시보드가 import) |
| `scripts/_tc_generate.py` | TC 초안 생성 작업: 제한된 `claude -p` 실행·검증·라이브러리 반영 | ❌ (대시보드가 스레드로 실행) |
| `scripts/_tc_fetch.py` | 원격 문서 수집용 안전한 GET (SSRF 방어) | ❌ (다른 스크립트가 import) |
| `scripts/_tc_html.py` | HTML·Confluence storage → markdown | ❌ (다른 스크립트가 import) |
| `scripts/_tc_credentials.py` | Confluence·Figma 자격증명 (마스킹·환경변수 우선) | ❌ (대시보드가 import) |
| `scripts/_tc_connectors.py` | PRD URL·Confluence·Figma 소스 수집 | ❌ (대시보드가 import) |
| `scripts/_tc_source_watch.py` | 출처 버전 변경 확인·차이·확인 완료 | ❌ (대시보드가 import) |
| `scripts/_tc_md_export.py` | TC 라이브러리 → testcases/{group}/tc_*.md (퍼널·그룹 매핑·tc_id 고정·드리프트, 반영·롤백은 TC 스튜디오) | ❌ (대시보드가 import) |

| `scripts/assert_guard.py` | 힐링 패치 후 assertion 약화 감지. `original_assertions`(최초) vs 현재 파일 비교 → 감소 시 경고 출력 | ✅ (`.venv/bin/python scripts/assert_guard.py`) |
| `scripts/jira_reporter.py` | 테스트 실패 시 Jira 이슈 자동 생성. 스크린샷·영상 첨부 포함. `config/jira_config.json` 또는 환경변수 `JIRA_TOKEN` 설정 필요. `99_merge.py`가 최종 실패 시 자동 호출 | ✅ (`.venv/bin/python scripts/jira_reporter.py [--group G] [--dry-run] [--all]`, `--all`은 이미 만든 이슈도 다시 생성) |
| `scripts/parse_cases.py` | `.md`/`.json` 테스트케이스 파일 파서 (YAML frontmatter 지원). frontmatter 문자열값의 따옴표 자동 제거 (`id: "CL_01"` → `CL_01`). Steps는 번호(`1.`) 형식 권장이나 번호 없는 평문 줄도 파싱 지원 | ❌ (run_qa.py가 import해서 사용) |
| `tests/unit/` | 저장소 단위 테스트 — `pipeline/` `hooks/` `core/` `dashboard/` `import_studio/` 영역별 폴더 (파서 테스트: `core/test_core_parsers.py`) | ❌ (`pytest`가 자동 실행) |
| `scripts/sync_test_data.py` | 프로덕트별 테스트 데이터 동기화 유틸 | ❌ (필요 시 import) |
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
| `test_data/{product}.json` | 테스트 입력값 중앙 관리. 테스트 코드에서 하드코딩 금지, 이 파일에서 읽어 사용 | `"valid_user": {...}` |

프로덕트별 파일 형식: `{ "data_key": { "username": "...", "password": "..." } }`
- 파일명은 프로덕트 이름이며 `load_test_data()`가 파일명을 최상위 키로 묶어 읽습니다.
- 테스트케이스 frontmatter의 `data_key`가 이 파일의 서브키를 참조
- 실제 입력값은 git에서 제외된 `test_data/{product}.json`에 저장합니다.

---

## 상태 파일 (실행 결과가 저장되는 곳)

| 파일 | 저장 내용 | 생성 시점 |
|---|---|---|
| `state/pipeline.json` | 단일 파이프라인 전체 상태 (dom_info, plan, review_summary, heal_context 등) | `run_qa.py` 실행 시 |
| `state/discuss.json` | 팀 토론 상태 (주제, 결론, 투표 항목) | 대시보드 토론 시작 시 |
| `agents/dialog.json` | **팀 자유 토론 대화 로그 전용** (QA 파이프라인 심의는 기록 안 함) | 팀 토론 시작 시 |
| [`agents/team_notes.md`](../../agents/team_notes.md) | 승인된 팀 결정사항 (구현 완료 후 초기화) | 토론 항목 전체 투표 완료 시 |
| [`agents/lessons_learned.md`](../../agents/lessons_learned.md) | 큐레이션된 실수 패턴 (수동 관리) | 힐링·코드리뷰 심의 완료 시 |
| [`agents/lessons_learned_auto.md`](../../agents/lessons_learned_auto.md) | 자동 기록 힐링 로그 (heal_utils.py) | 06_heal.py 실행 시 자동 |
| `pending_impl.json` | 승인 후 구현 대기 항목 (훅이 감지해 자동 구현) | 대시보드 전체 투표 완료 시 |
| `state/parallel.json` | 병렬 파이프라인 실행 결과 (targets, 통계) | `99_merge.py` 완료 시 |
| `state/quick.json` | 빠른 실행 결과 (병렬 상태와 분리) | `99_merge.py --quick` 완료 시 |
| `state/heal_context.json` | 병렬 파이프라인 힐링 컨텍스트 (에러 분류, failure_groups, skipped_repeated, lessons_snapshot 포함) | `99_merge.py` 실패 시 |
| `state/heal_stats.json` | 힐링 오류 패턴별 빈도 카운터 (Top 5를 심의 컨텍스트에 주입) | `06_heal.py` 실패 분석 시 |
| `state/run_history.json` | 실행 소유 ID·종료 상태·복구 안내·측정 결과·리포트 경로를 포함한 실행 이력 | 실행 결과 저장 및 작업 종료 시 갱신 |
| `state/runs/{run_id}/execution_result.json` | 실행 소유 결과. 최신 상태와 분리해 취소·중단·측정 결과 보존 | 각 실행 단계와 대시보드 종료 처리 |
| `state/dashboard_execution.json` | 대시보드 공통 실행 예약·소유 프로세스·종료 상태 | 실행 시작·재시작 복구·취소 시 |
| `logs/merge.txt` | 99_merge.py 실행 로그 | `99_merge.py` 실행 시 |
| `logs/quick_run.txt` | 빠른 실행 로그 | 대시보드 빠른 실행 시 |
| `logs/run_parallel.txt` | 병렬 파이프라인 실행 로그 | 대시보드에서 병렬 실행 시 |
| `logs/run_qa.txt` | 단일 파이프라인 실행 로그 | 대시보드에서 단일 실행 시 |
| `logs/run_qa_headless.txt` | `run_qa.py` headless 세션 전체 로그 | `run_qa.py` (--auto) 실행 시 |
| `logs/run_qa_parallel_headless.txt` | `run_qa_parallel.py` headless 세션 전체 로그 | `run_qa_parallel.py` (--auto) 실행 시 |
| `state/parallel_contexts.json` | 병렬 파이프라인 subagent 컨텍스트 전체 (dom_info + test_cases + shared_paths) | `run_qa_parallel.py` 실행 시 |


## 실행이 진행되지 않을 때 확인 순서

| 증상 | 먼저 확인할 곳 | 다음 작업 |
|---|---|---|
| Python 파일을 찾을 수 없음 | 현재 터미널 위치 | 프로젝트 루트로 이동 |
| Python 모듈 import 오류 | 사용 중인 Python 환경 | 해당 환경에 requirements 설치 여부 확인 |
| Claude 명령·로그인 오류 | 서버 PC의 CLI | CLI 설치·로그인 확인 후 새 오류 메시지 확인 |
| 케이스를 찾지 못함 | `--cases`, 그룹 폴더, 파일 확장자 | 실제 존재하는 경로와 `tc_*.md` 확인 |
| 병렬 대상이 누락됨 | `config/pages.json` 그룹과 폴더명 | 두 이름이 같은지, 케이스가 있는지 확인 |
| URL 분석 실패 | 실제 사이트 접속과 로그 | 주소·접근 권한·사이트 상태 확인 |
| 생성 코드의 데이터 키 오류 | TC의 data_key와 테스트 데이터 | 제품명·데이터셋 키·속성 이름을 비교 |
| 결과가 과거 값 같음 | 실행 시각과 로그 끝부분 | 새 실행이 시작됐는지 확인 |

로그를 읽을 때는 마지막 오류뿐 아니라 그 직전의 단계와 대상 그룹도 함께 확인합니다. 사용자에게는 오류 메시지와 입력한 실행 명령을 전달하되 계정 비밀번호·토큰은 제외합니다.

`state/pipeline.json`의 값을 직접 지워 완료 상태로 만들지 않습니다. 누적 실행·힐링 정보와 상태 전이 규칙이 있으므로 재실행·수정은 제공된 진입점과 운영 절차로 진행합니다. 에이전트의 실패 수정 절차는 [힐링 지침](../operations/HEALING_GUIDE.md)에 있습니다.
