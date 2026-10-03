# 힐링 가이드

> **문서 유형: 에이전트 운영 지침** · 테스트 실패 진단·수정 절차. TC 작성 사용자 매뉴얼과 별도로 사용합니다.
>
> **독자**: Claude Code — `06_heal.py` 또는 `99_merge.py` 실패 후 복구 가능 여부와 중단 조건을 확인합니다.
> 오류별 패치 참고: [Heal Patterns](../../.claude/skills/heal-patterns/SKILL.md). 아래 안전 정책을 먼저 적용합니다.

## 1차: 실행 소유권과 취소

- 대시보드의 단일·병렬·빠른 실행은 공통 실행 잠금으로 중복 실행을 막습니다. 실행 중 초기화도 같은 잠금에서 거부합니다.
- `QA_RUN_ID`는 실행 소유자, `QA_WORKFLOW_ID`는 전체 작업 식별자입니다. 자식 단계까지 유지합니다. 별도 `--state-path`를 쓰는 worker는 상태 경로에서 파생한 실행 ID를 사용합니다.
- 오류의 기준은 `state/runs/{run_id}/execution_result.json`입니다. 다른 실행의 최신 상태·리포트·스크린샷을 가져와 복구하지 않습니다. 소유 결과가 없거나 상태 소유자가 바뀌면 중단합니다.
- 취소는 해당 실행의 프로세스 그룹에 적용합니다. POSIX에서는 종료 신호 후 자식 그룹이 끝날 시간을 주고, 남은 프로세스만 강제 종료합니다. 자동 패치의 검증 중 SIGTERM·KeyboardInterrupt는 이번 시도 직전 파일을 복원합니다. 강제 종료(SIGKILL)는 Python 복원 코드를 실행할 수 없습니다.

## 2차: 실행 상태와 증거 보존

- 프로세스 종료 코드만으로 테스트 성공을 판정하지 않습니다. 저장된 실제 테스트 결과와 실행 상태를 확인합니다. 대시보드 재시작 후에도 실행 소유권과 종료 결과를 재확인합니다.
- `failed`, `cancelled`, `interrupted`, `timed_out`, `incomplete`는 작업 종료 상태입니다. `workflow_status`가 이 값이면 기존 `reviewed`·`heal_needed` 단계가 남아 있어도 훅은 다음 단계 지시를 주입하지 않습니다. 새 실행은 제공된 진입점에서 시작합니다.
- pytest 호출마다 `invocation_id`를 발급합니다. JSON 리포트는 실행별 경로에 저장하고 스크린샷·영상·Trace는 `{run_id}__{invocation_id}__` 접두어로 구분합니다. 다른 호출의 증거를 덮어쓰거나 폴더 전체를 초기화하지 않습니다.
- `--no-report`는 HTML 리포트 생성을 생략합니다. 실패 진단용 증거와 실행 결과는 계속 저장합니다.

## 3차: 제한된 복구와 즉시 중단

- **측정된 실패가 모두 Locator 오류일 때만 자동 복구합니다.** setup·call·teardown·수집 오류를 함께 확인합니다. 기대값 불일치, 브라우저 실행·세션·통신·설정 오류, 일반 타임아웃, 중단, 알 수 없는 오류가 하나라도 있으면 자동 패치를 중단합니다.
- pytest 비정상 종료(2·3·4·5·음수)는 일부 Locator 실패가 있더라도 자동 복구 대상이 아닙니다.
- 읽기 재시도는 알려진 일시적 통신 오류가 난 DOM 읽기에만 적용하며 최초 호출 포함 최대 3회입니다. 클릭·입력·저장·전체 pytest 실행을 통신 오류 처리로 반복하지 않습니다. pytest의 `rerunfailures` 플러그인도 실행과 복구 검증에서 비활성화합니다.
- `06_heal.py`는 저장된 JSON 리포트나 소유 오류를 읽습니다. 리포트가 없다고 `--lf`·전체 테스트를 다시 실행해 오류를 수집하지 않습니다. 실패 자체는 재실행 권한이 아닙니다.
- `06_auto_heal.py`는 캐시를 무시하고 현재 URL의 DOM을 새로 수집합니다. 복구를 위한 수집은 동적 클릭·호버 탐색을 건너뜁니다. 수집 실패·빈 DOM이면 패치와 검증을 시작하지 않습니다. 이전 `dom_info`·다른 실행의 화면으로 대체하지 않습니다.
- 변경한 파일은 파일당 한 번 검증합니다. 첫 미통과·크래시·타임아웃에서 이번 자동 패치로 변경한 파일을 원래 바이트로 복원하고 **다른 전략·파일·Agent 패치·추가 테스트 실행을 중단**합니다. `recovery_stopped=true` 또는 종료코드 **5**를 받으면 `06a_dialog.py`, `05_execute.py`, `99_merge.py`를 이어 실행하지 않습니다.

## CLI와 종료코드

기본 상태는 `state/pipeline.json`입니다. worker에서는 해당 상태 경로를 모든 명령에 동일하게 전달합니다.

```bash
.venv/bin/python scripts/05_execute.py --no-report --state-path state/worker.json
.venv/bin/python scripts/06_heal.py --state-path state/worker.json
# 06_heal 종료코드 10일 때만
.venv/bin/python scripts/06_auto_heal.py --state-path state/worker.json
# 자동 검증 실패 없이 미수정 실패가 남아 종료코드 1일 때만
.venv/bin/python scripts/06a_dialog.py --state-path state/worker.json
.venv/bin/python scripts/assert_guard.py --state-path state/worker.json
```

병렬·빠른 실행의 자동 복구는 `99_merge.py`가 아래 옵션으로 호출합니다.

```bash
.venv/bin/python scripts/06_auto_heal.py \
  --state-path state/parallel.json --state-key status \
  --heal-context-path state/heal_context.json
```

| 스크립트 | 코드 | 의미 |
|---|---|---|
| `06_heal.py` | 0 | 실패 없음 또는 힐링 대상 단계가 아님 |
| `06_heal.py` | 10 | 소유 실패 분석 완료, 복구 후보 준비 |
| `06_heal.py` | 2 | 복구 불가·타임아웃·반복 실패·횟수 초과 등으로 중단 |
| `06_auto_heal.py` | 0 | 자동 패치한 실패가 모두 검증 통과, 잔여 실패 없음 |
| `06_auto_heal.py` | 1 | 검증 실패 없이 미수정 후보가 남음 또는 적용 가능한 패턴 없음 |
| `06_auto_heal.py` | 3 | `heal_needed` 상태가 아니거나 실패 없음 |
| `06_auto_heal.py` | 5 | 새 DOM·소유권·복구 검증 문제로 자동 복구 중단 |
| `06a_dialog.py` | 5 | 이미 중단된 복구이므로 심의 생략 |

최대 3회 제한과 동일 오류 2회 반복 감지는 복구 후보가 남았을 때 적용합니다. 단일은 `06_heal.py`, 병렬·빠른 실행은 `99_merge.py`가 `heal_count`를 증가시킵니다. 검증 실패 후 남은 횟수를 소모하며 재시도하지 않습니다.

`05_execute.py --only-failed --no-report`는 안전하게 수정한 후보를 확인할 때 이전 실패만 선택하는 옵션입니다. 자동 복구가 중단된 작업에는 적용하지 않습니다. 전체 통과가 확인되고 중단 상태가 아닐 때 마지막 실행으로 HTML 리포트를 생성합니다.

## 복구 완료 확인과 시각 진단

1. 허용된 후보만 패치하고 변경 파일의 검증 통과를 확인합니다.
2. `assert_guard.py`로 assertion 약화를 확인합니다. 기대값을 바꿔 실패를 숨기지 않습니다.
3. `agents/lessons_learned.md`에 교훈을 기록합니다. 자동 로그는 `lessons_learned_auto.md`, 빈도 데이터는 `state/heal_stats.json`에 기록됩니다. `06a_dialog.py`가 Top 5 패턴을 전달합니다.
4. 현재 실행에 속한 스크린샷·Trace만 참고합니다. Trace는 `npx playwright show-trace <파일>.zip`으로 확인합니다.
5. 필요하면 `browser_navigate` → `browser_snapshot` → `browser_evaluate`로 새 페이지의 Locator를 확인합니다. 새 DOM 수집이 실패하면 중단합니다.

MCP 브라우저와 pytest 브라우저는 쿠키·상태를 공유하지 않습니다. 로그인·저장 등의 동작을 시각 진단용으로 반복하지 않습니다. `/oh-my-claudecode:ultraqa` 등 스킬을 사용해도 위 소유권·새 DOM·중단 규칙과 검증 횟수 제한을 그대로 지킵니다.
