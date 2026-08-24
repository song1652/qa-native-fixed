# QA-Native — 아키텍처 문서

> **독자**: 사람 — 내부 설계·아키텍처 문서. 에이전트가 읽지 않음.
> **Claude Code가 LLM 역할을 직접 수행하는 API-Free QA 자동화 파이프라인**

---

## 아키텍처 정의: Agent-Augmented Self-Referential Test Harness

전통적 테스트 하네스의 뼈대 위에 LLM 에이전트를 결합한 하이브리드 아키텍처.
하네스가 테스트를 '실행'할 뿐 아니라 '생성-검증-치유'까지 수행하는 자율적 QA 시스템.

### 하네스 엔지니어링 원칙 준수 (6개 중 5개)

| 원칙 | 준수 | 구현 |
|---|---|---|
| 파이프라인 오케스트레이션 | ✅ | scripts/01~06 순차 실행 |
| 중앙 상태 관리 | ✅ | state/pipeline.json |
| 실행-결과 분리 | ✅ | scripts=실행, pytest assertion=판정 |
| 환경 격리 | ✅ | conftest.py browser/context/page fixture |
| 결과 수집 자동화 | ✅ | 스크린샷, JSON/HTML 리포트 |
| 테스트 데이터 주입 분리 | 🔶 | 자체 완결 파일 원칙으로 대체 (힐링 격리성 우선) |

### 에이전트 확장 기능 (전통적 하네스에 없는 4가지)

1. **테스트 코드 자동 생성** — DOM 분석 → plan → 코드
2. **심의 기반 품질 게이트** — 사수/부사수 시뮬레이션 리뷰
3. **자가 치유(self-healing)** — 실패 시 코드 패치 후 재실행 루프
4. **DOM 기반 동적 전략 수립** — 정적 스크립트가 아닌 런타임 전략

### 구조적 특징: 샌드위치 패턴

결정론적 하네스 레이어와 비결정론적 에이전트 레이어가 교대로 등장.
Claude Code가 하네스의 두뇌이면서 자신의 산출물을 검증하는 자기참조(self-referential) 루프.

```
비결정론적: Plan 수립 (Claude)
결정론적:   코드 파일 생성 → 고정
결정론적:   Lint 검사 → 고정 규칙
비결정론적: 코드 리뷰 (Claude 심의)
결정론적:   pytest 실행 → 결정론적
비결정론적: 힐링 패치 (Claude)
결정론적:   재실행 → 결정론적
```

---

## 핵심 설계 원칙

| 원칙 | 내용 |
|---|---|
| **API-Free** | `anthropic`, `openai`, `langchain` 등 외부 LLM SDK 일절 미사용 |
| **Claude Code = 두뇌** | 전략 수립, 코드 작성, 리뷰, 실패 패치를 직접 수행 |
| **스크립트 = 실행 도구** | 01~06 스크립트는 DOM 추출·lint·pytest·결과 수집만 담당 |
| **state/pipeline.json 중심** | 모든 단계 결과가 하나의 파일에 누적 → 단계 간 컨텍스트 공유 |
| **단일 심의 Agent** | 사수/부사수 두 관점을 한 번의 Agent 호출로 내부 시뮬레이션 |
| **컨텍스트 주입** | `02a/03a/06a_dialog.py`가 파일을 병렬 읽기 후 JSON으로 출력 → Agent가 추가 파일 읽기 불필요 |

---

## 아키텍처

### 단일 파이프라인

```
┌────────────────────────────────────────────────┐
│               Claude Code (두뇌)                │
│  DOM 분석 해석 → 테스트 전략 수립                     │
│  테스트 코드 직접 작성                               │
│  실패 트레이스백 분석 → 코드 자동 패치                  │
│  FSM 전이 검증 + 반복 실패 자동 스킵                   │
└──────────────────┬─────────────────────────────┘
                   │  읽기 / 쓰기
                   ▼
         state/pipeline.json
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
  Python        Playwright   pytest
  스크립트      (브라우저)   (테스트 실행)
01~06_auto_heal.py Chromium  HTML 리포트
```

### 병렬 파이프라인

```
testcases/{group}/tc_*.md  (1파일 = 1케이스)
      ↓                     예: mysite/ (N개)
run_qa_parallel.py
      ↓
config/pages.json → URL 조회 + testcases/ 폴더 자동 스캔
      ↓
DOM 분석 (URL당 1회, 캐시)
      ↓
PARALLEL_SUBAGENT_CONTEXTS 출력
  { shared_context_paths: {파일경로...},  ← 공통 (1회)
    subagents: [{고유 데이터}, ...] }      ← 배치별
      ↓
오케스트레이터 Claude (Agent tool)
  ┌──────────┬──────────┬──────────┐
  │Subagent 1│Subagent 2│Subagent N│  ← 동시 실행
  │ tc_01    │ tc_02    │ tc_N     │
  │plan→코드  │plan→코드  │plan→코드  │
  └──────────┴──────────┴──────────┘
      ↓
  tests/generated/{group}/tc_{번호}_{english_snake_case}.py  저장
      ↓
parallel/99_merge.py
  pytest tests/generated/ 일괄 실행
  통합 HTML 리포트 생성
  실패 시 단일과 동일한 힐링 플로우:
    에러 분류 → 사이트 체크 → 반복 감지 → auto_heal → heal_context.json → 힐링 루프 (최대 3회)
```

### 심의 Agent 흐름 (Plan / Code Review / Healing)

```
*a_dialog.py 실행
  └─ team_charter.md, senior.md, junior.md, lessons_learned.md, 코드 병렬 읽기
  └─ DELIBERATION_CONTEXT_START ... END  JSON 출력

오케스트레이터 Claude가 JSON 추출
  └─ 심의 Agent 1회 호출 (사수/부사수 내부 시뮬레이션)
       └─ plan / review / patch 확정
       └─ state/pipeline.json 업데이트 (결과 저장)
       └─ 필요 시 agents/lessons_learned.md 교훈 수동 추가 (자동 로그는 lessons_learned_auto.md)

※ dialog.json은 팀 자유 토론 전용. QA 파이프라인 심의는 state/pipeline.json에만 기록됨.
```

### 팀 토론 흐름

```
대시보드 "토론 시작" 또는 run_team.py
  └─ team_discuss.py: 컨텍스트 수집 → DELIBERATION_CONTEXT 출력

Claude가 멀티라운드 티키타카 진행 (최소 3라운드)
  └─ 발언마다 agents/dialog.json에 즉시 append (Edit tool, 배치 금지)
  └─ 대시보드 SSE로 실시간 표시

결론 도출 → 사용자가 대시보드에서 항목별 승인/반려
  └─ 승인 시: team_notes.md 저장 + pending_impl.json 생성
  └─ 훅(check_pending_impl.py) → Claude가 자동 구현
```

---

## 스킬 프레임워크 & OMC 통합

`.claude/skills/`에 정적 가이드라인을 공식 SKILL.md 표준으로 관리. 스킬 목록·OMC 적용 단계 상세는 [`CLAUDE.md`](../CLAUDE.md) "스킬 프레임워크 & OMC 적용" 섹션 참조.

동적 빈도 데이터는 `state/heal_stats.json`에 기록. `06_heal.py`가 실패 시 자동 업데이트하고, `06a_dialog.py`가 Top 5 빈출 패턴을 DELIBERATION_CONTEXT에 주입.

---

## Healer (자가 치유)

테스트 실패 시 `06_heal.py`가 traceback을 수집하고 Claude Code가 패치합니다. 최대 3회 자동 시도.
첫 실행 포함 모든 실행은 `--no-report`로 실행하며, 전체 통과 확인 후 마지막 1회만 리포트를 생성합니다.
스크린샷은 최종 실패 시에만 저장됩니다 (매 실행 전 초기화).
실패 스크린샷이 heal_context에 자동 연결되며, traceback만으로 원인 불명확 시 Playwright MCP 도구로 실제 페이지의 현재 DOM/텍스트를 확인할 수 있습니다.

> 힐링 완료 체크리스트·MCP 시각 검증 절차는 [`doc/HEALING_GUIDE.md`](HEALING_GUIDE.md) 참조.
> 오류 유형별 패치 전략은 `.claude/skills/heal-patterns/SKILL.md` 참조.

---

## 최적화 기법

### DOM 병렬 수집 (01_analyze.py)
- **단일 브라우저**: 메인 URL(networkidle+30s) + 서브페이지(load+500ms, Semaphore(8)) 단일 브라우저에서 분석
- **React 컴포넌트 추출**: `components`, `idElements` 객체 구조화
- **DOM 캐시**: URL 해시 기반 `state/dom_cache/` 캐싱, TTL 7일 (env: `DOM_CACHE_TTL_HOURS`)
- **--force-refresh**: 캐시 무시 강제 재분석 플래그

### 병렬 테스트 실행 (05_execute.py)
- **최대 4 workers** — pytest-xdist 기반 병렬 실행 (spa: true 사이트는 세션 충돌 방지를 위해 1 worker 고정)
- **--only-failed 플래그** — 이전 실패 케이스만 선별 재실행
- **--no-report 모드** — 힐링 루프 중 리포트 생성 스킵 (전체 통과 후 최종 1회만)

---

## 기술 스택

Python 3.12 / Playwright (Chromium) / pytest / flake8 / Claude Code (API 없음)

> 대시보드: Python ThreadingHTTPServer + SSE + Vanilla JS (포트 8766, CORS는 localhost만 허용)
> Overview에 Heal Stats 도넛 차트 + Top 빈출 패턴 시각화 포함
> 루트 스크립트(run_qa.py 등)는 `_bootstrap.py`로 scripts/ 경로를 자동 설정
> 상세 API·기능: [`SCRIPTS_GUIDE.md`](SCRIPTS_GUIDE.md) 참조
