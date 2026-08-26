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

### `run_qa.py`
| 옵션 | 설명 |
|------|------|
| `--url <URL>` | 테스트 대상 URL |
| `--cases <path>` | 케이스 파일/폴더 경로 |

### `run_team.py`
| 옵션 | 설명 |
|------|------|
| `--topic <str>` | 토론 주제 (생략 시 대화형 입력) |

---

## 대시보드 API (포트 8766)

### 실행 트리거 (POST)

| 엔드포인트 | 바디 | 설명 |
|---|---|---|
| `/api/run_qa` | `{ url, cases_dir }` | 단일 파이프라인 실행 |
| `/api/run_qa_parallel` | `{}` | 병렬 파이프라인 실행 |
| `/api/run_merge` | `{ group?, quick?, no_heal? }` | 99_merge.py 실행 |
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
| `/api/team/start` | 팀 토론 시작 (`{ topic }`) |
| `/api/team/vote` | 결론 항목 투표 (`{ item_id, vote }`) |
| `/api/team/reject` | 토론 반려 (`{ reason }`) |
| `/api/import/convert` | Excel → 테스트케이스 변환 (`{ file, sheets }`) |

### SSE (Server-Sent Events)

| 엔드포인트 | 이벤트 | 설명 |
|---|---|---|
| `/api/events` | `state_update` | pipeline.json / discuss.json 변경 시 실시간 푸시 |
