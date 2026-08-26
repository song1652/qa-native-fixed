# state/pipeline.json 구조

> **독자**: Claude Code — pipeline.json / 관련 state 파일 스키마를 확인해야 할 때 on-demand 참조.
> 헬링 중 실패 구조 파악, 새 필드 추가 시, state 읽기/쓰기 코드 작성 전에 확인.

```json
{
  "url": "",
  "test_cases": [],
  "step": "init | analyzed | planned | generated | reviewed | done | heal_needed | heal_failed | timeout",
  "dom_info": {
    "title": "",
    "url": "",
    "inputs": [],
    "buttons": [],
    "errors": [],
    "links": [],
    "navItems": [],
    "hidden_elements": [],
    "components": [],
    "idElements": [],
    "testidElements": [],
    "dynamic_elements": [],
    "contextmenu_elements": [],
    "forms_count": 0,
    "selector_note": "selectors 우선순위: id > testid > aria_label > placeholder > name > text > css > xpath"
  },
  "sub_dom_keys": {
    "{sub_url}": "{url_md5_hash}"
  },
  "dom_cache_key": "state/dom_cache/{url_md5_hash}.json",
  "plan": [],
  "cases_path": "testcases/{group}/",
  "group_dir": "{group}",
  "generated_file_path": "tests/generated/{group}/",
  "generated_files": [],
  "lint_result": {},
  "review_summary": "",
  "rejection_count": 0,
  "execution_result": {
    "passed": 0,
    "failed": 0,
    "total": 0,
    "pass_rate": 0.0,
    "exit_code": 0,
    "heal_count": 0,
    "json_report_path": "/tmp/qa_single_report_{ts}.json"
  },
  "heal_count": 0,
  "heal_context": {
    "heal_count": 0,
    "failure_count": 0,
    "failures": [
      { "test_id": "", "test_name": "", "traceback": "", "error_type": "Locator", "screenshot": { "path": "", "url": "", "timestamp": "", "trace_path": "", "console_errors": [], "network_failures": [] } }
    ],
    "failure_groups": { "Locator": ["test_a"], "Assertion": ["test_b"] },
    "skipped_repeated": ["test_name_1"],
    "url": "",
    "raw_tail": "",
    "analyzed_at": "",
    "mcp_snapshot_recommended": false,
    "mcp_snapshot_url": ""
  }
}
```

## state/heal_context.json 구조 (병렬 파이프라인)

단일 파이프라인과 동일한 힐링 플로우를 공유. `99_merge.py`가 생성/관리.

```json
{
  "heal_count": 1,
  "failure_count": 3,
  "failures": [
    { "test_id": "", "test_name": "", "file": "", "traceback": "", "error_type": "Locator", "screenshot": { "path": "", "url": "", "timestamp": "", "trace_path": "", "console_errors": [], "network_failures": [] } }
  ],
  "failure_groups": { "Locator": ["test_a"], "Assertion": ["test_b"] },
  "skipped_repeated": ["test_c"],
  "urls": { "heroku": "https://..." },
  "lessons_snapshot": "(최신 lessons_learned 스냅샷, 최대 3000자)",
  "analyzed_at": "ISO datetime"
}
```

| 필드 | 설명 |
|------|------|
| `failure_groups` | 에러 유형별 실패 테스트 그룹 (Agent가 같은 유형 일괄 처리) |
| `skipped_repeated` | 동일 오류 2회 연속 반복으로 스킵된 테스트 목록 |
| `urls` | 실패 테스트의 그룹별 URL (pages.json에서 조회) |
| `lessons_snapshot` | 힐링 시점의 lessons_learned + _auto 스냅샷 (subagent 간 학습 공유) |
| `screenshot.trace_path` | 실패 TC의 Playwright Trace 경로 (`tests/traces/*.zip`). 사람이 `npx playwright show-trace <파일>`로 시각 확인용 |
| `screenshot.console_errors` | 실패 시점까지 수집된 콘솔 에러·경고 목록 `[{type, text}]`. heal agent가 직접 읽음 |
| `screenshot.network_failures` | 실패 시점까지 수집된 네트워크 실패 목록 `[{url, method, status, failure}]`. heal agent가 직접 읽음 |

## state/heal_stats.json 구조

```json
{
  "version": 1,
  "description": "힐링 오류 패턴별 빈도 카운터",
  "patterns": {
    "{error_type}::{summary}": {
      "count": 1,
      "error_type": "Locator | Assertion | Timeout | URL | JS평가 | Python런타임 | Playwright일반 | 기타",
      "summary": "핵심 오류 라인 (최대 120자)",
      "first_seen": "ISO datetime",
      "last_seen": "ISO datetime"
    }
  }
}
```

## state/run_history.json 구조

매 실행(단일/병렬) 완료 시 `append_run_history()`가 자동으로 한 줄씩 추가하는 배열.

```json
[
  {
    "timestamp": "YYYY-MM-DD HH:MM:SS",
    "pipeline": "single | quick",
    "group": "{group_name}",
    "groups": ["{group_a}", "{group_b}"],
    "passed": 10,
    "failed": 0,
    "skipped": 0,
    "total": 10,
    "pass_rate": 100.0,
    "heal_count": 0,
    "first_pass": true,
    "duration_sec": 12.3,
    "per_test_results": {
      "test_fn": "pass"
    }
  }
]
```

| 필드 | 설명 |
|------|------|
| `pipeline` | `single` (05_execute.py 단일 파이프라인) 또는 `quick` (99_merge.py --quick 빠른 실행) |
| `skipped` | pytest가 skip한 테스트 수 |
| `per_test_results` | 테스트 함수명(nodeid의 `::` 이후 부분) → `"pass"` \| `"fail"` \| `"skip"` 매핑 (대시보드 필터링용) |
| `group` | 단일 파이프라인: 대상 그룹명 |
| `groups` | 병렬 파이프라인: 실행된 그룹 목록 |
| `first_pass` | 힐링 없이 첫 실행 통과 여부 (생성 코드 품질 프록시) |
| `duration_sec` | pytest 포함 전체 소요 시간 (초) |

## dom_info 필드 상세

각 요소의 `selectors` 객체는 9가지 전략을 포함: `{ id, testid, aria_label, role, placeholder, name, text, css, xpath }` (해당 속성이 있는 경우만 포함)

| 필드 | 설명 |
|------|------|
| `inputs[]` | input/textarea/select 요소 (visible + hidden 포함). `{ selectors, type, visible, required, disabled, value }` |
| `buttons[]` | 버튼·[role=button]·[role=menuitem] (visible + hidden 포함). `{ selectors, text, type, visible, disabled }` |
| `errors[]` | [role=alert/status], .error, .alert 등 에러·상태 영역. `{ selectors, role, live, text, visible }` |
| `links[]` | 텍스트가 있는 a[href] 요소. `{ selectors, text, href, visible }` (최대 50개) |
| `navItems[]` | 사이드바·메뉴 li 항목 (nav li, aside li, [role="treeitem/menuitem"] 등). `{ selectors, text, visible, href }` (최대 50개) |
| `hidden_elements[]` | 숨겨진 모달·드롭다운 컨테이너. `{ selectors, tag, role, trigger, children_count, children[] }` (최대 30개). `children`에 내부 버튼/링크/li 포함 |
| `components[]` | React/UI 컴포넌트: tab, checkbox, radio, tree, modal, select 등. 각 항목은 `{ type, selectors, text/label, visible, ... }` |
| `idElements[]` | 페이지 내 모든 [id] 요소 (visible + hidden). `{ id, tag, role, visible, text }` (최대 150개) |
| `testidElements[]` | data-testid/data-test/data-cy/data-qa 속성을 가진 요소. `{ attr, testid, selector, tag, text, visible }` (최대 50개). `attr`은 실제 속성명 |
| `dynamic_elements[]` | hover·click 트리거 후 노출된 요소 목록. `{ trigger: { selector, action, text, tag }, revealed: [...] }` |
| `contextmenu_elements[]` | 우클릭 후 나타난 컨텍스트 메뉴 항목. `{ trigger: { selector, action, text, tag }, revealed: [...] }` |

## sub_dom_keys 필드

서브페이지 URL → 캐시 해시 매핑. `01_analyze.py`가 서브페이지를 분석한 뒤 `state/dom_cache/{hash}.json`에 저장하고, 경로 대신 해시만 pipeline.json에 기록한다.
실제 서브 DOM은 `_paths.resolve_sub_doms(state)`로 캐시 파일에서 로드한다. (pipeline.json에 인라인 저장하지 않음)

## execution_result 필드 상세

| 필드 | 설명 |
|------|------|
| `passed` | 통과 테스트 수 |
| `failed` | 실패 테스트 수 |
| `total` | 전체 테스트 수 |
| `pass_rate` | 통과율 (%) |
| `exit_code` | pytest 종료코드 (0=성공, 1=실패) |
| `heal_count` | 이 execution에서 적용된 힐링 횟수 |
| `json_report_path` | pytest-json-report 파일 경로 (06_heal.py가 재활용, 삭제하지 않음) |

| `failure_groups` | 에러 유형별 실패 테스트 그룹 (단일 파이프라인에서도 Agent 일괄 처리용) |
| `mcp_snapshot_recommended` | `true`이면 heal agent가 `browser_snapshot`으로 실시간 DOM 확인 권장 (Locator/Assertion/Timeout 오류 시 자동 설정) |
| `mcp_snapshot_url` | MCP 스냅샷 대상 URL (`mcp_snapshot_recommended=true`일 때만 값 존재) |

## 힐링 프로세스

- `heal_count` (top-level): 06_heal.py만 증가시킴 (05_execute.py는 읽기만 함). 최대 3회 제한.
- `execution_result.heal_count`: 현재 state의 heal_count 값을 복사 (05_execute.py가 기록 시점의 스냅샷).
- 초과 시 `step = "heal_failed"`, 종료코드 2로 파이프라인 중단.

## state/discuss.json 구조 (팀 토론)

`run_team.py` 또는 대시보드 "토론 시작" 버튼 클릭 시 생성. `team_discuss.py`가 관리.

```json
{
  "topic": "토론 주제",
  "stage": "team_discussion",
  "status": "in_progress | approved | rejected",
  "step": "approved | rejected",
  "rejection_count": 0,
  "rejection_reason": "",
  "conclusion_items": [
    { "id": 1, "text": "결론 항목", "vote": "approved | rejected | null" }
  ]
}
```

## state/parallel.json 구조 (병렬 파이프라인)

`parallel/99_merge.py`가 생성·관리. 빠른 실행 시에는 `state/quick.json`에 동일 구조로 저장.

```json
{
  "status": "\"\" | init | analyzing | ready | error | testing | done | heal_needed | heal_failed",
  "step": "done",
  "execution_result": {
    "passed": 237,
    "failed": 3,
    "total": 240,
    "pass_rate": 98.8,
    "report_path": null,
    "report_name": null,
    "group_results": {
      "{group}": {
        "passed": 117,
        "failed": 3,
        "tests": [
          { "nodeid": "tests/generated/{group}/tc_*.py::test_fn", "name": "test_fn", "passed": true }
        ]
      }
    }
  },
  "targets": [
    { "group_dir": "{group}", "group_label": "{group}", "batch_info": "",
      "url": "https://...", "output_path": "tests/generated/{group}", "case_count": 120 }
  ]
}
```

| 필드 | 설명 |
|------|------|
| `status` | 병렬 파이프라인 현재 상태 (대시보드 표시용) |
| `execution_result.group_results` | 그룹별 개별 테스트 pass/fail 목록 |
| `targets` | 실행 대상 그룹·URL·케이스 수 목록 (`group_dir`/`group_label`/`batch_info`/`url`/`output_path`/`case_count`) |

## state/quick.json 구조 (빠른 실행)

`parallel/99_merge.py --quick` 실행 시 생성. `state/parallel.json`과 동일한 구조.
대시보드 "빠른 실행" 탭에서만 표시되며 `parallel_state`에 영향을 주지 않음.

---

## step 전이 규칙

`_pipeline_registry.py`의 `VALID_TRANSITIONS` 맵에 정의 (P35 이후 단일 소스). `write_state()`가 `pipeline.json` 기록 시 자동으로 `assert_valid_transition()`을 호출하여 잘못된 전이를 방지.

```
init → analyzed → generated → reviewed → done
                                    ↓         ↓
                               timeout     heal_needed → done (패치 성공)
                                    ↓           ↓         ↓
                                   done     timeout   heal_failed (3회 초과, 종료 상태)
                                                ↓
                                        done | heal_needed
```
