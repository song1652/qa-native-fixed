# API & CLI 레퍼런스

> **독자**: 사람 — 스크립트 CLI 옵션 및 대시보드 API 엔드포인트 완전 목록.

---

## 스크립트 CLI 옵션

### `scripts/01_analyze.py`
| 옵션 | 설명 |
|------|------|
| `--force-refresh` | DOM 캐시 무시, 강제 재분석 |

### `scripts/05_execute.py`
| 옵션 | 설명 |
|------|------|
| `--no-report` | HTML 리포트·스크린샷 생성 건너뜀 (힐링 중간 실행용) |
| `--only-failed` | 이전 실행에서 실패한 테스트만 재실행 |
| `-n <int>` | pytest-xdist 워커 수 지정 (기본 8) |

### `parallel/99_merge.py`
| 옵션 | 설명 |
|------|------|
| `--group`, `-g` | 실행할 그룹 폴더명 (생략 시 전체) |
| `--quick` | 빠른 실행 모드 (`state/quick.json` 저장, parallel_state 미변경) |
| `--no-heal` | 힐링 생략, 실패해도 done 처리 |
| `--no-report` | HTML 리포트·Jira 이슈 생성 건너뜀 (힐링 중 중간 실행용) |

### `run_qa.py`
| 옵션 | 설명 |
|------|------|
| `--url <URL>` | 테스트 대상 URL |
| `--cases <path>` | 케이스 파일/폴더 경로 |

### `run_team.py`
| 옵션 | 설명 |
|------|------|
| `--topic <str>` | 토론 주제 (생략 시 대화형 입력) |

### `agents/dashboard/serve.py`
| 옵션 | 설명 |
|------|------|
| `--host <host>` | 바인딩 주소 (기본 `127.0.0.1`) |
| `--port <int>` | 바인딩 포트 (기본 `8766`) |

환경 변수:

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `ALLOWED_HOSTS` | `localhost:8766,127.0.0.1:8766` | 허용할 HTTP `Host` 값. 쉼표 또는 공백으로 여러 값을 구분 |
| `ALLOWED_ORIGIN` | `http://localhost:8766` | POST 요청의 허용 `Origin`/`Referer` origin |
| `REMOTE_MODE` | 비활성 | `1`, `true`, `yes`, `on`이면 원격 모드 위험 API를 기본 차단 |
| `REMOTE_API_ALLOWLIST` | 빈 값 | 원격 모드에서 예외 허용할 API 패턴의 쉼표 구분 목록 |

`REMOTE_API_ALLOWLIST`의 각 항목은 `*`가 없으면 **경로 전체 exact match**,
마지막 문자가 `*`이면 `*` 앞 문자열에 대한 **prefix match**입니다. 중간 `*`, `?`,
문자 클래스 같은 일반 glob 문법은 지원하지 않습니다. 쿼리 문자열은 매칭 전에 제거됩니다.

---

## 대시보드 API (기본 포트 8766)

`REMOTE_MODE`가 비활성일 때는 기존 API 동작이 유지됩니다. 활성화하면 실행/초기화처럼
프로세스 또는 상태를 변경하는 위험 API가 HTTP 403으로 차단되고,
`REMOTE_API_ALLOWLIST`에 exact/prefix 패턴으로 명시된 경로만 허용됩니다. 조회 API와
토론 승인/반려 API는 원격 모드에서도 계속 사용할 수 있습니다. 이 설정은 인증을
대체하지 않으므로 외부 공개 시 별도의 인증 프록시가 필요합니다.

### 실행 트리거 (POST)

| 엔드포인트 | 바디 | 설명 |
|---|---|---|
| `/api/run_qa` | `{ url, cases_dir }` | 단일 파이프라인 실행 |
| `/api/run_qa_parallel` | `{}` | 병렬 파이프라인 실행 |
| `/api/run_merge` | `{ group?, quick?, no_heal?, no_report? }` | 99_merge.py 실행 |
| `/api/run_quick` | `{ groups: [], no_heal? }` | 빠른 실행 |
| `/api/run_log` | `{ log: "파일명" }` | 실행 로그 조회 |

### 상태 조회 (GET)

| 엔드포인트 | 반환 | 설명 |
|---|---|---|
| `/api/pipeline_state` | pipeline.json 전체 | 단일 파이프라인 상태 |
| `/api/batch_state` | `{ parallel_state, generated_files }` | 병렬 파이프라인 상태 |
| `/api/quick_state` | quick.json 전체 | 빠른 실행 상태 |
| `/api/generated_groups` | `{ groups: [{name, files}] }` | tests/generated/ 그룹 목록 |
| `/api/pages` | `{ pages, groups }` | pages.json + testcases 그룹 |
| `/api/reports` | `[{ name, path, mtime }]` | HTML 리포트 목록 |
| `/api/run_history` | run_history.json 전체 | 실행 이력 배열 |
| `/api/heal_stats` | heal_stats.json 전체 | 힐링 오류 패턴 통계 |
| `/api/pipeline_registry` | `{ pipeline: {steps, step_labels, step_compat}, parallel: {steps, step_labels} }` | `_pipeline_registry.py` 상수 노출 — constants.js가 fetch해 전역 변수 갱신 (P45) |
| `/api/coverage` | coverage.json (없으면 실시간 생성) | 테스트 커버리지 매트릭스 |
| `/api/flaky_tests` | flaky_tests.json | Flaky 테스트 목록 |
| `/api/import/files` | Excel 파일 목록 | import/ 폴더 파일 |

### 상태 변경 (POST)

| 엔드포인트 | 설명 |
|---|---|
| `/api/reset` | pipeline.json 초기화 |
| `/api/run_history/reset` | run_history.json 초기화 |
| `/api/heal_stats/reset` | heal_stats.json 초기화 |
| `/api/discuss/start` | 팀 토론 시작 (`{ topic }`) |
| `/api/discuss/vote_item` | 결론 항목 투표 (`{ item_id, status }`) |
| `/api/discuss/reject` | 토론 반려 |
| `/api/import/convert` | Excel → 테스트케이스 변환 (`{ file, sheets }`) |

### 원격 모드 위험도 분류

| 분류 | 엔드포인트 | 원격 모드 기본값 |
|---|---|---|
| 프로세스 실행/제어 | `/api/run_qa`, `/api/run_qa_parallel`, `/api/run_merge`, `/api/run_quick`, `/api/run_log` | 차단 (allowlist 필요) |
| 전역 초기화 | `/api/reset`, `/api/reset/all` | 차단 (allowlist 필요) |
| 파이프라인별 초기화 | `/api/pipeline/reset`, `/api/parallel/reset`, `/api/quick/reset`, `/api/run_history/reset`, `/api/heal_stats/reset`, `/api/discuss/reset` | 차단 (allowlist 필요) |
| 승인 게이트 | `/api/discuss/vote_item`, `/api/discuss/reject` | 허용 |
| 토론/설정/가져오기 변경 | `/api/discuss/start`, `/api/pages/add`, `/api/pages/update`, `/api/pages/delete`, `/api/import/convert` | 허용; 배포 환경에서 인증 프록시로 별도 통제 권장 |

예시:

```bash
# 단일 실행과 모든 reset 엔드포인트만 예외 허용
REMOTE_MODE=true \
REMOTE_API_ALLOWLIST='/api/run_qa,/api/reset*,/api/pipeline/reset,/api/parallel/reset,/api/quick/reset,/api/run_history/reset,/api/heal_stats/reset,/api/discuss/reset' \
python agents/dashboard/serve.py --host 0.0.0.0 --port 8800
```

### P0-3 동적 포트 상태

현재 저장소에는 동시에 실행 가능한 dashboard job 수에 대한 명시적 상한이나
workspace 생성/종료 수명주기가 없습니다. 따라서 포트 범위, 충돌 방지 레지스트리,
종료 시 해제를 묶는 P0-3 설계는 아직 결정할 수 없습니다. P0-1의 `--port`는
결정-independent 기반으로 제공하지만, job별 자동 포트 할당은 concurrency cap과
workspace lifecycle의 단일 소스가 정해질 때까지 보류합니다.

### SSE (Server-Sent Events)

| 엔드포인트 | 이벤트 | 설명 |
|---|---|---|
| `/api/events` | `state_update` | pipeline.json / discuss.json 변경 시 실시간 푸시 |
