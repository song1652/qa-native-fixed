# 웹 대시보드 디자인 교체 — 인수인계

> **독자**: 이 작업을 이어받는 LLM(Claude Code 또는 다른 모델)과 작업자.
> **작성**: 2026-10-02 · **저장소**: `/Users/junghoyoung/qa-native-fixed` (main)
> **한 줄 요약**: 대시보드의 모든 화면과 리포트 HTML을 **보라색 어두운 테마 → 밝은 테마**로 바꾼다. **기능·동작은 바꾸지 않는다.**

## 0. 먼저 읽을 것

| 순서 | 파일 | 내용 |
|---|---|---|
| 1 | 이 문서 | 목표, 규칙, 화면↔코드 대응, 작업 순서, 검증 |
| 2 | [`mockups/index.html`](mockups/index.html) | **디자인 시안 47장 목록.** 각 화면은 단독 HTML이라 브라우저로 열 수 있고, 소스(인라인 스타일)가 곧 명세다 |
| 3 | [`tokens.css`](tokens.css) | 새 색·글꼴·크기 변수. 그대로 붙여 쓴다 |
| 4 | 저장소 [`CLAUDE.md`](../../../CLAUDE.md) | 저장소 공통 규칙 (상태 파일은 `update_state`, 레지스트리 상수 등) |

디자인 원본은 claude.ai 디자인 캔버스다 — 웹: `https://claude.ai/artifact/Vg2a2GGdffjV1osgQqyH9y`, 기준이 된 앱 가이드: `https://claude.ai/artifact/XvGF3Gvyaw8M9uYQiFcbqe`. **비공개 링크라 다른 사람·모델은 열 수 없을 수 있다.** 그래서 같은 내용을 `mockups/`에 파일로 넣었다. 링크가 안 열리면 `mockups/`만 기준으로 삼는다.

## 1. 디자인 가이드 (요약 — 상세는 `mockups/Tokens.html`, `mockups/Components.html`)

**색** — `tokens.css` 변수만 쓴다. 컴포넌트 안에 hex를 쓰지 않는다.

| 쓰임 | 변수 | 값 |
|---|---|---|
| 페이지 바탕 / 카드 / 표 머리 | `--bg` / `--surface` / `--surface-sub` | `#F5F6F8` / `#FFFFFF` / `#F0F2F5` |
| 선 / 입력 테두리 | `--border` / `--border-input` | `#E2E5EA` / `#8B93A1` |
| 글자 본문 / 보조 / 힌트 | `--text` / `--text-2` / `--text-3` | `#111827` / `#4B5563` / `#6B7280` |
| 강조(주 버튼·링크·선택) | `--accent` / `--accent-bg` | `#1F4FD1` / `#E8EEFC` |
| 통과 / 실패 / 주의 | `--pass(-bg)` / `--fail(-bg)` / `--warn(-bg)` | `#15803D` / `#B91C1C` / `#92400E` (+ 연한 배경) |
| 로그 | `--log-bg` | `#F8F9FB` |

**글꼴** — 본문 IBM Plex Sans KR, 숫자·ID·시간·경로·로그 JetBrains Mono (Google Fonts). 크기: 화면 제목 22/600, 모달·상세 제목 17/600, 카드 제목 15/600, 본문 14, 보조 13, 라벨 12.

**배치** — 상단 바 56px(흰색, 아래 선) · 왼쪽 사이드바 232px(흰색) · 본문 여백 `28px 32px` · 카드 안 16px · 섹션 사이 20px. 모서리: 배지 4 / 버튼·입력 6 / 카드 8 / 모달 10. 그림자는 모달·토스트만. 버튼·입력 높이 34~36px, 주 실행 버튼 44px.

**부품 규칙**
- 주 버튼(파란 채움)은 **화면에서 다음에 누를 것 하나만**. 나머지는 흰 바탕 + 테두리.
- 비활성 버튼은 `title`로 이유를 알린다.
- 상태 배지는 항상 **글자**를 함께(통과·실패·중단·추정·가져옴·초안…). 색만으로 구분하지 않는다.
- 세그먼트(필터 토글)는 선택된 칸만 검은 채움(`#111827`).
- 되돌릴 수 없는 작업은 브라우저 `confirm()` 대신 **화면 안 대화창**(`mockups/DashDialogs.html`).
- 빈 상태는 선 아이콘 + 제목 + 한 줄 설명 + 다음 행동 버튼(`mockups/EmptyStates.html`).

**금지** — 보라색·그라데이션·글로우·유리(반투명) 효과 · 이모지 아이콘 · 영어 대문자 라벨(`ALL PASS`, `PASS RATE`, `TOTAL` → `모두 통과`, `통과율`, `전체`) · 색으로만 상태 구분.

**메뉴 구성(사이드바)** — 개요: 대시보드 / TC 작성: TC 스튜디오 / 실행: 빠른 실행, 단일 파이프라인, 병렬 파이프라인 / 결과: 리포트, 실행 기록 / 팀 토론: 새 토론 시작, (토론 목록) / 맨 아래: 페이지 URL 관리. 상단 바: 제품명 · 서버·파이프라인 상태 · 마지막 실행 · 오른쪽 `빠른 실행` 버튼. 지금의 `LIVE` 표시와 시계는 상태 문구로 바꾼다.

## 2. 지켜야 할 것 (절대)

1. **동작을 바꾸지 않는다.** API 호출, 상태 전이, 폴링, 저장 로직은 그대로. 바뀌는 것은 마크업 구조·클래스·CSS·문구뿐.
2. **`id`, `data-id`, `aria-*`, `role`은 유지한다.** TC 스튜디오만 `data-id`가 약 250개 있고 E2E 테스트가 이것으로 요소를 찾는다. 바꿔야 하면 테스트를 같은 커밋에서 고친다.
3. **테스트를 약하게 고치지 않는다.** 문구가 바뀌어 기대값을 고치는 것은 되지만, 검사 줄을 지우거나 `skip`하지 않는다. 시각 테스트는 새 디자인 기준으로 갱신한다.
4. 목업에 없는 상태가 코드에 있으면 **가장 가까운 목업의 부품을 조합**해 그린다. 새 색·새 부품을 만들지 않는다.
5. 목업 숫자·이름(그룹명, 건수)은 예시다. 실제 화면은 데이터 그대로.
6. 커밋은 단계(아래 4절)마다, 한국어 conventional commit. **push는 사용자에게 확인받는다.**
7. 기능 버그를 발견하면 고치되 디자인 커밋과 섞지 않는다(별도 커밋). `agents/lessons_learned.md`에는 기록하지 않는다(파이프라인 힐링 전용).

## 3. 화면 ↔ 목업 ↔ 코드

| 화면 | 목업 (`mockups/…html`) | 바꿀 코드 |
|---|---|---|
| 공통 틀(상단 바·사이드바) | 모든 화면 공통 | `agents/dashboard/index.html`, `static/css/layout.css`, `static/js/components/sidebar.js`, `static/js/router.js`(뷰 전환만, 동작 유지) |
| 토큰·공통 부품 | `Tokens`, `Components`, `EmptyStates`, `DashDialogs` | `static/css/variables.css`(53줄, 보라 테마), `static/css/components.css`(560), `static/css/animations.css`(604, 글로우 대부분 삭제) |
| 대시보드 | `Main`, `MainTrend`, `MainEmpty` | `static/js/views/overview.js`, `static/css/views/overview.css` |
| 빠른 실행 | `QuickRun`, `QuickRunRunning`, `QuickRunFail` | `static/js/views/quick-run.js`, `views/quick-run.css`, `static/js/components/group-result.js`, `test-list.js` |
| 실패 상세 | `FailureInspector` | `static/js/components/failure-detail.js`, `static/css/failure-detail.css` |
| 단일 파이프라인 | `SingleIdle`, `SinglePipeline`, `SingleHealing`, `SingleFailed` | `static/js/views/pipeline.js`, `views/pipeline.css` |
| 병렬 파이프라인 | `ParallelReady`, `ParallelRunning`, `ParallelPipeline` | `static/js/views/parallel.js`, `views/parallel.css` |
| 리포트 목록 | `Reports` (+ `DashDialogs` 리포트 삭제) | `static/js/views/reports.js`, `views/reports.css` |
| 실행 기록 | `History` | `static/js/views/history.js`, `views/history.css` |
| 팀 토론 | `TeamNew`, `TeamSession`, `TeamVote` | `static/js/views/team.js`, `views/team.css` |
| 페이지 URL 관리 | `Pages`, `PagesEdit` | `static/js/views/pages.js`, `views/pages.css` |
| TC 스튜디오 ①~④ | `TcGenerate`, `TcGenerateReady`, `TcGenerating`, `TcLibrary`, `TcLibraryBulk`, `TcDetailTabs`, `TcReview`, `TcReviewDup`, `TcExport`, `TcExportChecked`, `TcMdPreview` | `static/js/tc-studio/*.js`(10개), `static/css/tc-studio.css`(상단 `.tc-studio` 변수 블록이 자체 보라 테마 — `tokens.css` 값으로 교체) |
| TC 스튜디오 모달 | `TcImport`, `TcImportMapping`, `TcImportPlan`, `TcImportHistory`, `TcProfileEditor`, `TcTrash`, `TcModalsA`, `TcModalsB` | 같은 폴더의 `import.js`, `main.js`, `generate.js`, `library.js`, `detail.js` |
| 리포트 HTML (새 탭) | `ReportPass`, `ReportFail`, `ScreenshotOverlay` | `scripts/report_html.py`(702줄, `report_css()`·`build_report()`), `parallel/_report.py`(`build_parallel_html()`) — 파이프라인이 `tests/reports/`에 만드는 독립 HTML |

참고: 모든 경로는 `agents/dashboard/` 아래(리포트 생성기 제외). 화면 JS 상당수가 인라인 `style=`을 쓴다(`overview.js` 32곳, `quick-run.js` 28곳 등). 인라인 색은 클래스로 옮기거나 토큰 변수로 바꾼다.

**TC 스튜디오 전용 메모**
- 지금은 탭이 번호 원(①②③④) 스테퍼다. 목업은 **밑줄 탭**(`기획 정보 · 생성 / 라이브러리 N / 초안 검토 N / 내보내기`)이다. 목업을 따른다. `data-id="nav-tab-*"`는 유지.
- 표·트리·상세 패널의 기능(셀 편집, 끌어다 놓기, 가상 스크롤, 열 접기)은 그대로 두고 색·선·글꼴만 바꾼다.
- 상세 패널의 `가져옴` 칩·잠긴 검토 상태, `문체 확인` 태그, 영구삭제 2단계 확인 등 최근 기능은 목업에 그려져 있다.

## 4. 작업 순서

각 단계: 목업 확인 → 코드 수정 → 관련 테스트 → 서버 재시작(파이썬을 고쳤을 때) → 브라우저에서 목업과 나란히 비교 → 커밋.

- [x] **1. 토큰·글꼴 교체** — `tokens.css` 내용을 `variables.css`에 반영하고 기존 변수 이름을 새 이름으로 연결(또는 사용처 일괄 교체). `index.html`에 글꼴 `<link>`. `body` 배경 그라데이션 제거. 이 단계만으로 화면이 대략 밝아져야 한다.
- [x] **2. 공통 틀** — 상단 바·사이드바를 목업대로. 메뉴 묶음·순서 변경(1절). 활성 메뉴는 `--accent-bg` 배경.
- [x] **3. 공통 부품** — 버튼·배지·입력·표·카드·세그먼트·단계 표시·토스트·빈 상태·확인 대화(`components.css`). `animations.css`의 글로우·빛나는 효과 제거(필요한 회전·페이드만 남김). `confirm()` 사용처를 화면 안 대화창으로.
- [x] **4. 화면별** — 대시보드 → 빠른 실행·실패 상세 → 단일 → 병렬 → 리포트 목록 → 실행 기록 → 팀 토론 → 페이지 URL. 화면마다 1커밋.
- [x] **5. TC 스튜디오** — `tc-studio.css` 변수 블록 교체 → 상단(제목·스위트·탭) → 라이브러리 → 생성 → 검토 → 내보내기 → 모달. 2~3커밋으로 나눈다.
- [x] **6. 리포트 HTML** — `report_html.py`의 CSS와 마크업, `parallel/_report.py`. 실패 TC 펼침(오류 요약·단계·기대 결과·스크린샷·영상·trace)은 `ReportFail` 목업대로.
- [x] **7. 마무리** — 전체 테스트, 사용자 설명서 화면 캡처 7장 재촬영(`doc/guides/tc-studio/images/tc-studio-user-guide/`), 남은 보라색 검색.

## 5. 검증

```bash
cd /Users/junghoyoung/qa-native-fixed
# 전체 단위·E2E (약 3.5분, 905건 통과가 기준)
python3 -m pytest tests/unit -q -W ignore -p no:cacheprovider
# 대시보드 서버 재시작 (파이썬 수정 시. JS·CSS는 새로고침만 — 서버가 no-cache를 보냄)
kill $(lsof -tiTCP:8766 -sTCP:LISTEN); nohup python3 agents/dashboard/serve.py --port 8766 >/tmp/dash8766.log 2>&1 &
# 남은 옛 테마 색 찾기 (0건이 목표)
grep -rniE "8b5cf6|7c3aed|a78bfa|#08071b|#0b0b14|rgba\(139, ?92, ?246|rgba\(88, ?40, ?180|linear-gradient|radial-gradient|ALL PASS|PASS RATE" agents/dashboard/static agents/dashboard/index.html scripts/report_html.py parallel/_report.py
```

- `tests/unit/dashboard/test_view_layout_e2e.py`: 모든 화면의 제목 위치·크기·글꼴·본문 폭이 같은지 검사한다. 제목 클래스(`.pipeline-title`, `.page-title`, `.ov-heading`, `.hist-heading`)를 바꾸면 이 테스트의 선택자도 함께 바꾸고, **새 기준(본문 여백 28·32px, 22px/600 제목)으로 기대값을 맞춘다.**
- TC 스튜디오 E2E(`tests/unit/tc_library/*_e2e.py`)는 `data-id`로 요소를 찾는다. 2절 2번 규칙.
- 시각 확인: Playwright로 화면을 찍어 같은 이름의 목업과 비교한다. 예: `mockups/QuickRun.html` ↔ `http://localhost:8766/?view=quick_run`.
- 리포트 HTML은 `python3 scripts/05_execute.py` 실행 후 `tests/reports/`에 생긴 파일을 열어 `ReportPass`/`ReportFail`과 비교한다(실제 사이트 접속이 필요 없는 그룹: `tc_studio_demo`는 `http://localhost:8877` 정적 서버 — `python3 -m http.server 8877 --directory tests/fixtures/tc_studio_demo`).

## 6. 완료 정의

- 4절 체크박스 전부 완료, 전체 테스트 통과(기대값 갱신은 근거와 함께).
- 5절 옛 색 검색 0건.
- 모든 화면이 같은 틀(상단 바·사이드바·제목 위치)을 쓰고, 목업과 나란히 봤을 때 색·글꼴·간격·부품이 같다.
- 사용자 설명서 캡처 교체.
- 범위 밖: `qa-native-app` 저장소(앱 대시보드는 이미 같은 가이드로 별도 진행), 기능 추가.

## 7. 새 세션 시작 문구 (복사해서 붙여 넣기)

```text
/Users/junghoyoung/qa-native-fixed 저장소에서 작업해.
doc/development/design-refresh/HANDOFF.md를 처음부터 끝까지 읽고, mockups/index.html과 tokens.css를 확인한 다음
4절 작업 순서의 1단계부터 진행해줘.
- 기능·동작은 바꾸지 말고 디자인만 바꿔. id·data-id·aria는 유지해.
- 단계마다 목업과 실제 화면을 Playwright 스크린샷으로 나란히 비교하고, 테스트 결과와 함께 짧게 보고한 뒤 다음 단계로 넘어가.
- 커밋은 단계마다 하고 push는 나한테 물어봐.
- 설명은 한국어로 쉽고 짧게.
```


## 8. 구현·검증 기록 (2026-10-02)

- 공통 토큰·틀·부품, 대시보드 8종, TC 스튜디오 4탭·모달, 단일·병렬 리포트 HTML을 적용했다.
- API 호출, 저장, 상태 처리, 폴링과 기존 테스트 코드는 변경하지 않았다. 기존 `id`·`data-id`·`aria-*`·`role` 속성을 시작 커밋과 비교하여 누락이 없는지 확인했다. 그라데이션을 제거한 추이 그래프의 `areaGrad` 식별자도 유지했다.
- 최종 전체: `python3 -m pytest tests/unit -q -W ignore -p no:cacheprovider` → **905 passed, 1 skipped** (225.57초).
- 5절의 옛 테마 검색 **0건**, 제공 팔레트 밖의 6자리 색상 **0건**, 기존 요소 식별자·접근성 속성 누락 **0건**.
- TC 스튜디오 전용: `python3 -m pytest tests/unit/tc_library -q -W ignore -p no:cacheprovider` → **226 passed**.
- 화면 비교 파일: `/tmp/tc-design-refresh-*/*comparison.png`. 단일·병렬, TC 스튜디오, 리포트의 실행 중·실패·검토 상태 중 일부는 브라우저 안에서만 검증 데이터를 사용했다. 설명서 검토 화면도 브라우저용 초안으로 촬영했으며 저장된 TC를 바꾸지 않았다.
- 실제 리포트 생성: 저장소 스크립트와 로컬 예제 `tc_studio_demo`를 임시 프로젝트 `/tmp/tc-design-refresh-report-pipeline`에 복사해 `scripts/05_execute.py`를 실행했다. 정상 실행 **5 passed**, 임시 복사본에 실패 조건을 넣은 실행 **4 passed / 1 failed**. 원본 테스트와 실제 파이프라인 상태·이력은 유지했다. 병렬 렌더러도 정상 실행 결과로 확인했다.
- 리포트에서 필터, 페이지 이동(25건), 상세 펼침, 스크린샷 확대·닫기, 영상 조작·다운로드 요소, trace 명령 복사를 Playwright로 확인했다. 브라우저 오류 **0건**.
- 설명서 화면 7장을 재촬영하고 탭 이름·강조색 설명을 갱신했다.
- 지정된 검색에 잡히지 않던 훅 실행 안내 6종의 어두운 색·이모지를 공통 확인 대화창 부품으로 교체했다. 확인 버튼과 배경 클릭 닫기를 검증했다.

### 목업과 달라지는 부분

- 목업에만 있고 기존 화면에 없는 조작(리포트 인쇄 버튼 등)은 추가하지 않았다. 기존 검토 카드·작성 규칙 편집·리포트 접기 구조는 유지하면서 목업의 색·글꼴·간격·부품을 적용했다.
- 이미 저장된 예전 리포트 HTML은 생성 당시의 디자인을 유지한다. 새로 생성하는 리포트부터 밝은 테마가 적용된다.
- 진행 중 전체 실행에서 기존 화면 전환의 비동기 타이밍으로 리포트 선택 테스트가 한 차례 실패했다. 해당 테스트와 전체 실행을 다시 확인했으며 테스트를 변경하거나 약하게 만들지 않았다.
- push·병합은 수행하지 않았다.

### 작업 트리의 별도 변경

마지막 확인에서 이번 마무리 작업이 작성하지 않은 추가 변경이 `agents/dashboard/index.html`, `agents/dashboard/static/css/layout.css`, `agents/dashboard/static/css/views/overview.css`에 있었다. 기존 추가 변경을 보존하고 마무리 커밋에서는 제외했다. 최종 전체 테스트는 이 작업 트리에서 통과했다.
