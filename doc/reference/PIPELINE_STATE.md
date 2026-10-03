# state/pipeline.json 구조

> **문서 유형: 상태 레퍼런스** · 런타임 상태의 구조와 전이 규칙. 운영 절차는 [힐링 지침](../operations/HEALING_GUIDE.md)을 참고합니다.

> **독자**: Claude Code — pipeline.json / 관련 state 파일 스키마를 확인해야 할 때 on-demand 참조.
> 헬링 중 실패 구조 파악, 새 필드 추가 시, state 읽기/쓰기 코드 작성 전에 확인.

## 실행 소유권과 최신 화면 상태

`pipeline.json`, `parallel.json`, `quick.json`은 현재 화면에 보여 줄 최신 실행의 상태입니다. 실행별 결과의 저장 위치는 `state/runs/<run_id>/execution_result.json`입니다. 새 작업의 상태가 예전 작업의 늦은 응답으로 덮이지 않도록 최신 상태를 변경할 때 소유 ID를 함께 확인합니다. 모든 상태 갱신은 `update_state(path, mutator)`의 잠금 안에서 처리합니다.

| 공통 필드 | 설명 |
|---|---|
| `run_id` | 해당 상태 파일을 현재 소유하는 실행 ID. 대시보드 시작 시 새 ID로 교체 |
| `last_run_id` | 최신 테스트 실행 결과의 소유 ID. 결과를 화면 상태에 반영할 때 `run_id`와 함께 확인 |
| `workflow_status` | 대시보드가 관리하는 전체 작업의 `running`, `passed`, `failed`, `cancelled`, `timed_out`, `interrupted`, `incomplete` 상태. `step`·병렬 `status` FSM과 별도 |
| `execution_result` | 해당 ID에 속하는 측정 결과·오류·복구 안내. 시작 시 예전 결과를 제거하며 완료 시 현재 소유 ID가 일치할 때만 저장 |

새 대시보드 실행은 `workflow_status=running`을 기록하고 이전 `execution_result`, `error`, `heal_subagent_contexts`를 제거합니다. URL·생성 파일 경로 등 실행 설정은 유지합니다. 힐링 횟수 초기화는 기존 새 실행 준비 규칙에 따르며 결과 정리 과정에서 임의로 리셋하지 않습니다. 전체 작업이 실패했지만 이미 측정한 테스트는 통과했을 수 있으므로 결과 건수만으로 전체 완료 여부를 판단하지 않습니다.

단일 파이프라인의 `step`과 병렬·빠른 실행의 `status`는 `_pipeline_registry.py`에 정의된 값을 사용합니다. 대시보드의 중단·시간 초과를 표시하려고 FSM에 `cancelled` 같은 새 문자열을 넣지 않습니다. 상단과 실행 화면은 `workflow_status`와 `execution_result.status`를 함께 확인합니다.

## state/dashboard_execution.json 구조

대시보드의 단일·병렬·병렬 결과 실행·빠른 실행이 공유하는 실행 예약입니다. 시작·중단·상태 조정·파이프라인 초기화가 같은 파일 잠금을 사용합니다. 빈 환경에서는 빈 객체가 저장될 수 있습니다.

```json
{
  "run_id": "<server-issued-id>",
  "tag": "run_qa | run_qa_parallel | run_merge | run_quick",
  "pipeline": "single | parallel | quick",
  "groups": ["login"],
  "status": "running",
  "started_at": "ISO datetime",
  "started_epoch": 0.0,
  "pid": 12345,
  "process_identity": "<process birth and process group identity>",
  "log_name": "<run_id>.txt"
}
```

종료 시 `finished_at`, 종료 `status`, `error`를 추가합니다. 종료를 아직 확인하지 못했으면 `stopping:true`와 `stop_status`를 보존해 새 실행을 막습니다. PID만으로 소유권을 판단하지 않으며 프로세스 생성 정보로 재사용된 PID를 구분합니다.

서버 재시작 후 살아 있는 소유 실행과 하위 프로세스 그룹은 계속 예약을 차지합니다. 프로세스가 끝난 뒤에는 해당 실행의 저장된 결과를 사용하며, 종료 결과가 없으면 `interrupted`로 저장합니다. 비정상 launcher 종료는 중간 테스트 통과 결과가 있어도 전체 작업을 실패로 표시하고 측정 건수를 유지합니다. 남은 파이프라인 단계를 자동 시작하지 않습니다.

대시보드에서 시작한 전체 작업은 시작 시점부터 **3600초**로 제한합니다. 초과 시 하위 작업을 정리하고 `timed_out` 결과를 보존합니다. POSIX 중단은 TERM 후 전체 프로세스 그룹이 사라질 때까지 최대 3초 기다리고, 필요하면 KILL 후 종료를 확인합니다. 하위 코드 복구 작업의 정리 시간을 확보하며, 그룹 종료를 확인하기 전에는 예약을 해제하지 않습니다.

## 실행별 결과와 시도별 자료

| 경로·필드 | 소유권과 수명 |
|---|---|
| `state/runs/<run_id>/execution_result.json` | 한 실행의 최신 결과. 내부 `run_id`가 디렉터리 ID와 일치해야 읽음 |
| `state/runs/<run_id>/execute/<invocation_id>/pytest_report.json` | 매 pytest 호출의 별도 JSON. 같은 실행의 힐링 재시도도 새 `invocation_id` 사용 |
| `logs/runs/<run_id>.txt` | 대시보드 launcher의 소유 로그 |
| `logs/runs/<run_id>-headless.txt` | 존재하는 경우 같은 실행의 Claude 자동 실행 로그 |
| `QA_RUN_ID`·`QA_WORKFLOW_ID` | launcher에서 자식으로 전달하는 실행·전체 workflow ID |
| `QA_INVOCATION_ID`·`QA_ARTIFACT_PREFIX` | pytest 시도 ID와 증거 파일의 실행·시도별 접두어 |

병렬 worker의 개별 상태는 루트 ID와 해당 상태 경로에서 파생한 worker ID로 분리합니다. `workflow_id`는 같은 전체 작업을 연결하며 `run_id`는 결과의 실제 소유자를 구분합니다. 이전 시도의 JSON·스크린샷 메타데이터를 현재 실행의 성공 증거로 사용하지 않습니다. HTML 리포트와 스크린샷·영상·Trace도 실행·시도를 구별하는 이름으로 저장합니다.

`scripts/run_results.py`의 원자적 결과 쓰기는 이미 저장된 `cancelled`, `interrupted`, `timed_out`을 후속 늦은 실행 결과가 덮지 못하게 합니다. HTML 리포트가 없어도 결과 JSON과 실행 기록은 보존합니다. 실행별 자료의 자동 만료·일괄 정리 정책은 현재 제공하지 않습니다. DOM 캐시의 TTL과 리포트 선택 삭제는 별도 기능입니다.

## state/pipeline.json 예시

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

단일·병렬·빠른 실행의 결과와 대시보드가 조정한 실패·중단을 `append_run_history()`가 원자적으로 추가하는 배열입니다. 같은 실행의 여러 시도는 이력에 여러 항목으로 남을 수 있습니다. 리포트 파일 유무로 기록을 필터링하지 않습니다.

```json
[
  {
    "timestamp": "YYYY-MM-DD HH:MM:SS",
    "pipeline": "single | parallel | quick",
    "run_id": "<execution-id>",
    "workflow_id": "<root-workflow-id>",
    "invocation_id": "<pytest-invocation-id>",
    "status": "passed",
    "report_path": null,
    "recovery": {"category": "unknown", "title": "", "message": "", "action": "inspect_log", "can_heal": false, "read_retryable": false},
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
| `pipeline` | `single`, `parallel`, `quick` 실행 유형 |
| `run_id`·`workflow_id`·`invocation_id` | 결과 소유 실행·전체 작업·pytest 시도 ID. 이전 기록이나 pytest 전에 중단한 작업에는 일부 필드가 없을 수 있음 |
| `status` | `passed`, `failed`, `cancelled`, `timed_out`, `interrupted`, `incomplete`. 측정 건수와 별도로 실행 완료 여부를 판단 |
| `report_path` | 해당 실행의 HTML 파일 경로. 생성하지 못했거나 `--no-report`이면 이력에서 `null` |
| `recovery`·`errors`·`error` | 공유 오류 분류의 원인·다음 행동과 실제 오류 자료. 테스트 준비 중 실패도 보존 |
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
| `exit_code` | pytest 종료코드. 0=완료, 1=테스트 실패, 2=중단/수집 오류, 3=내부 오류, 4=옵션 오류, 5=테스트 없음. 종료코드와 오류 단계를 함께 판단 |
| `heal_count` | 이 execution에서 적용된 힐링 횟수 |
| `json_report_path` | 해당 `run_id`·`invocation_id`의 pytest JSON 경로. 힐링에서 소유 ID·요약·테스트 목록을 검증한 뒤 읽음 |
| `run_id`·`workflow_id`·`invocation_id` | 실행 결과의 소유 ID, 전체 workflow ID, 이번 pytest 호출 ID |
| `started_at`·`finished_at` | 해당 호출의 시작·종료 시각 |
| `status` | 테스트 수와 별도의 실행 결과 상태. 준비 실패·중단·시간 초과도 표현 |
| `report_path`·`report_name` | 이번 시도의 HTML 자료. 미생성 시 빈 값 또는 `null` |
| `errors` | 실패한 setup·call·teardown 단계와 테스트 수집 오류를 모두 포함 |
| `recovery` | `{category,title,message,action,can_heal,read_retryable}`. 다른 실행의 오류로 채우지 않음 |

| `failure_groups` | 에러 유형별 실패 테스트 그룹 (단일 파이프라인에서도 Agent 일괄 처리용) |
| `mcp_snapshot_recommended` | `true`이면 heal agent가 `browser_snapshot`으로 실시간 DOM 확인 권장 (Locator/Assertion/Timeout 오류 시 자동 설정) |
| `mcp_snapshot_url` | MCP 스냅샷 대상 URL (`mcp_snapshot_recommended=true`일 때만 값 존재) |

## 힐링 프로세스

- `heal_count` (top-level): 06_heal.py만 증가시킴 (05_execute.py는 읽기만 함). 최대 3회 제한.
- `execution_result.heal_count`: 현재 state의 heal_count 값을 복사 (05_execute.py가 기록 시점의 스냅샷).
- 초과 시 `step = "heal_failed"`, 종료코드 2로 파이프라인 중단.
- 자동 힐링은 실제 실패가 모두 수정 가능한 Locator 오류로 분류된 경우에만 허용합니다. Assertion·환경·세션·통신·설정·중단·시간 초과·불명 오류가 섞이면 `recovery_stopped`와 원인 안내를 보존하고 중단합니다. `heal_failed`만으로 힐링 횟수 초과를 단정하지 않습니다.
- 힐링 전 실행 ID가 일치하는 pytest JSON의 요약·노드·실패 단계가 저장된 결과와 일치하는지 확인합니다. 무관한 JSON이나 기존 리포트를 수정 근거로 사용하지 않습니다.
- 분석 단계의 알려진 DOM 읽기만 재시도 가능한 통신 오류에서 총 최대 3회 시도합니다. 클릭·입력·이동 또는 pytest 전체 실행은 이 정책으로 자동 반복하지 않습니다.

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
