# QA Automation — Claude Code Native

> **독자**: 사람 — 신규 진입점. 설치·실행 방법과 내부 문서 링크 모음.

API 비용 없이 Claude Code 토큰만으로 동작하는 QA 자동화 시스템.
DOM 분석 → 테스트 코드 자동 생성 → 심의 → 실행 → 자가 힐링까지 전 과정 자동화.

---

## 실행 파일 목록

| 파일 | 언제 실행? | 하는 일 |
|---|---|---|
| `run_qa.py` | 단일 URL 테스트 시작 | state/pipeline.json 생성 후 Claude에게 파이프라인 실행 지시 |
| `run_qa_parallel.py` | 여러 URL 동시 테스트 | pages.json 기반 워커 생성 + 병렬 실행 지시 |
| `run_team.py` | 팀 토론 주제 등록 | state/discuss.json 생성 (대시보드 버튼으로 대체 가능) |
| `agents/dashboard/serve.py` | 모니터링 대시보드 실행 | http://localhost:8766 에서 파이프라인 실행·모니터링·토론 관리 |
| `scripts/06_auto_heal.py` | 자동 패치 (힐링 선 실행) | 06_heal.py 이후 Agent 호출 전 deterministic 패턴 자동 수정 |
| `parallel/99_merge.py` | 병렬 실행 완료 후 | pytest 일괄 실행 + HTML 리포트 생성 + workers 정리 |
| `parallel/99_merge.py --quick --group` | 빠른 실행 (대시보드) | 특정 그룹만 pytest 실행 (state/quick.json에 결과 저장) |

> **scripts/ 폴더 안의 파일들은 직접 실행하지 않습니다.** Claude가 파이프라인 순서에 따라 자동으로 호출합니다.

---

## 사전 요구사항

| 항목 | 최소 버전 | 확인 방법 |
|------|----------|----------|
| **Python** | 3.12+ | `python --version` |
| **Node.js** | 18+ | `node --version` |
| **Claude Code CLI** | 최신 | `claude --version` |

> API 키 불필요. Claude Code 토큰만 사용합니다.

---

## 설치

### 1. Python 패키지

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Playwright MCP (힐링 단계 실시간 DOM 확인용)

```bash
claude mcp add playwright -- npx -y @playwright/mcp@latest
```

설치 확인:

```bash
claude mcp list
# playwright: npx -y @playwright/mcp - ✓ Connected  가 표시되면 정상
```

> **Claude Code CLI 설치**: [claude.ai/code](https://claude.ai/code) 또는 `npm install -g @anthropic-ai/claude-code`

---

## 실행

```bash
# 폴더 지정 (권장) — 폴더 내 tc_*.md 파일 전체를 자동 읽음
python run_qa.py --url https://example.com/login --cases testcases/login/
```

케이스 수에 따라 자동 분기됩니다:

| 케이스 수 | 동작 |
|---|---|
| 1개 | 단일 파이프라인 — `state/pipeline.json` 생성 후 Claude Code가 순차 실행 |
| N개 | 병렬 파이프라인 — 케이스별 worker 자동 생성, Claude Code가 동시 실행 |

---

## 테스트 케이스 작성

케이스는 `testcases/` 하위 그룹 폴더에 `.md` 파일로 작성합니다. **1파일 = 1케이스.**

```
testcases/
  {서비스명}/     ← 케이스 그룹 (URL은 config/pages.json 참조)
    tc_01_login_success.md
    tc_02_wrong_password.md
    ...
```

**케이스 파일 형식 (YAML frontmatter + Markdown):**

```markdown
---
id: tc_01
data_key: valid_user
priority: high
tags: [positive, smoke]
type: structured
---
# 정상 로그인 성공

## Precondition
0. 로그인 페이지 접속 상태

## Steps
1. username 필드에 test_data[valid_user].username 입력
2. password 필드에 test_data[valid_user].password 입력
3. Login 버튼 클릭

## Expected
- You logged into a secure area! 메시지가 표시되어야 한다.
```

- frontmatter 필수: `id`, `data_key`, `priority`, `tags`, `type`
- Steps 입력값은 `test_data[{data_key}].{속성}` 형식 (하드코딩 금지)

자세한 작성 규칙: [`doc/TEST_CASE_GUIDE.md`](doc/TEST_CASE_GUIDE.md)

---

## 병렬 파이프라인 직접 실행 (선택)

```bash
python run_qa_parallel.py
# pages.json + testcases/ 자동 스캔 → PARALLEL_SUBAGENT_CONTEXTS 출력
# 공통 참조(lessons_learned 등)는 파일 경로로, 고유 데이터만 JSON으로 전달
# Claude Code가 subagents[] 각 항목을 동시 실행 (코드 생성)
python parallel/99_merge.py
# pytest 일괄 실행 + HTML 리포트 생성
```

---

## 산출물

| 파일 | 내용 |
|---|---|
| `tests/generated/{group}/{label}.py` | Claude Code가 작성한 테스트 코드 |
| `tests/reports/parallel_index_{ts}.html` | 통합 HTML 리포트 |
| `tests/screenshots/*.png` | 최종 실패 케이스 스크린샷 (힐링 완료 후 실패 시만 저장) |

---

## 파일 구조

> 전체 디렉토리 트리: [`doc/DIRECTORY.md`](doc/DIRECTORY.md)

| 폴더 | 역할 |
|---|---|
| `scripts/` | 파이프라인 단계별 스크립트 + 훅 + 라이브러리 (Claude가 자동 호출) |
| `agents/` | 사수-부사수 역할, 팀 토론 로그, lessons_learned |
| `prompts/` | 심의 Agent 프롬프트 템플릿 |
| `state/` | 런타임 상태 파일 (pipeline.json, run_history.json 등) |
| `config/` | 설정 (pages.json, test_data.json) |
| `testcases/` | 테스트 케이스 `.md` 파일 (그룹별 서브폴더) |
| `tests/` | 생성된 테스트 코드, 리포트, 스크린샷 |
| `.claude/skills/` | 스킬 프레임워크 (SKILL.md 표준) |

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `state/pipeline.json 없음` | 파이프라인 초기화 미실행 | `run_qa.py` 또는 `run_qa_parallel.py` 재실행 |
| `tests/generated/` 파일 없음 | subagent 코드 생성 미완료 | Claude Code에 subagent 재실행 요청 |
| 특정 케이스 FAIL | assertion / locator 오류 | 해당 `.py` 파일 직접 확인 후 수정, 또는 Healer 재실행 |
| 스크린샷 미생성 | conftest.py 중복 로드 | `tests/generated/` 하위에 conftest.py 없어야 함 |
| 힐링 3회 반복 실패 | selector/assertion 불일치 | MCP로 실제 페이지 DOM 확인 (`browser_navigate` → `browser_snapshot`) |
| `browser_snapshot` 도구 없음 | Playwright MCP 미설치 | `claude mcp add playwright -- npx -y @playwright/mcp@latest` 실행 후 재시작 |
| 병렬 힐링 후 lessons_learned 누락 경고 | 힐링 패치만 적용, 교훈 미기록 | `agents/lessons_learned.md`에 교훈 수동 기록 후 `99_merge.py` 재실행 (자동 로그는 `lessons_learned_auto.md`에 별도) |
| DOM 분석 실패 | 네트워크 / URL 오류 | URL 접근 가능 여부 확인 |

---

## 대시보드 (선택)

```bash
python agents/dashboard/serve.py
# http://localhost:8766
```

단일/병렬 파이프라인 실행, 빠른 실행, 팀 토론, 리포트 열람, 실행 로그 모니터링 지원.

> 대시보드 기능 상세 · API 엔드포인트: [`doc/SCRIPTS_GUIDE.md`](doc/SCRIPTS_GUIDE.md) 참조

---

## 내부 문서 (`doc/`)

> `doc/` 폴더는 **사람 전용** 상세 문서 공간입니다. 에이전트(Claude)가 읽지 않습니다.

| 파일 | 내용 |
|---|---|
| [`doc/SCRIPTS_GUIDE.md`](doc/SCRIPTS_GUIDE.md) | **모든 .py 파일 역할·실행 방법 정리** |
| [`doc/PROJECT_OVERVIEW.md`](doc/PROJECT_OVERVIEW.md) | 아키텍처·설계 의도 상세 |
| [`doc/TEST_CASE_GUIDE.md`](doc/TEST_CASE_GUIDE.md) | 테스트케이스 작성 규칙 |
| [`doc/HEALING_GUIDE.md`](doc/HEALING_GUIDE.md) | 힐링 패치 기준·MCP 시각 검증 절차 |
| [`doc/TEAM_DISCUSSION.md`](doc/TEAM_DISCUSSION.md) | 팀 토론 파이프라인 상세 |
| [`doc/PIPELINE_STATE.md`](doc/PIPELINE_STATE.md) | state/pipeline.json 전체 스키마 |
| [`doc/DIRECTORY.md`](doc/DIRECTORY.md) | 프로젝트 디렉토리 트리 |
