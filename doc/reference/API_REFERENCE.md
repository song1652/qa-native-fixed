# API & CLI 레퍼런스

> **문서 유형: 개발 레퍼런스** · CLI 인자와 대시보드 API 계약. 사용 순서는 [스크립트 사용 매뉴얼](../guides/SCRIPTS_GUIDE.md)에 있습니다.

> **독자**: 사람 — 스크립트 CLI 옵션 및 대시보드 주요 API 엔드포인트 목록.

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

워커 수는 케이스 수와 사이트 설정에 따라 자동 선택하며 최대 4입니다. 이 스크립트의 CLI에는 `-n` 옵션이 없습니다.

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
| `/api/reports/delete` | HTML 리포트 삭제 (`{ names: ["report.html"] }`) |
| `/api/import/convert` | Excel → 테스트케이스 변환 (`{ file, sheets }`) |

#### 리포트 삭제

`POST /api/reports/delete`는 `names`에 지정한 `tests/reports/`의 HTML 파일을
삭제합니다. 유효한 요청은 HTTP 200과 함께
`{ "ok": true|false, "deleted": [...], "missing": [...], "failed": [{ "name":
"...", "error": "..." }] }`를 반환합니다. 이미 없는 파일은 `missing`에 넣고,
개별 파일 삭제가 실패하면 `failed`에 기록한 뒤 나머지 파일을 계속 처리합니다.
`failed`가 하나라도 있으면 `ok`는 `false`입니다. 같은 이름을 여러 번 보내면 최초
순서를 유지하며 한 번만 처리합니다.

`names`가 비어 있거나 배열이 아니거나, 항목이 문자열이 아니거나, 안전한 단일
파일명이 아니거나, 소문자 `.html` 확장자가 아니거나, 심볼릭 링크이면 HTTP 400과
`{ "ok": false, "error": "...", "code": "INVALID_REPORT_NAMES" }`를
반환합니다. 모든 항목을 검증한 뒤 삭제를 시작하므로 잘못된 이름이 하나라도 있으면
정상 파일도 삭제하지 않습니다. 심볼릭 링크는 링크 자체와 대상 파일을 모두 보존합니다.
### TC 스튜디오 라이브러리 (`/api/tc-library`)

`routes_tc_library.py`가 처리한다. 쓰기 요청은 모두 CSRF 검사를 받고, 케이스 쓰기는 `rev`가 맞아야 한다 (틀리면 409 + `server_case`). JSON 바디 상한 2MB, xlsx 업로드 25MB (초과 시 413 `PAYLOAD_TOO_LARGE`). 스위트 이름에 경로 문자가 있으면 400 `INVALID_SUITE`.

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/tc-library` | 스위트 목록 `{suites:[{suite, sheets, count}]}` |
| POST | `/api/tc-library/import/preview?filename=&mapping=` | 본문 = xlsx 바이트. `mapping`은 URL 인코딩 JSON. 시트별 헤더 행·케이스 수·경고 + `preview_id` |
| POST | `/api/tc-library/import/plan` | `{suite, sources:[{preview_id,sheets,prefixes,sheet_mappings?}]}` → `{run_id,status,rows,summary}`. 단일 `{preview_id,suite,sheets,prefixes}`도 지원 |
| POST | `/api/tc-library/import` | `{run_id,skip:[case_id],overwrite:[case_id]}` → `{run_id,suite,status,created,updated,unchanged,skipped}`. 기존 단일 파일 본문 호환 지원 |
| GET | `/api/tc-library/import/runs` | Excel→라이브러리 작업 목록 `{runs,errors}` |
| GET | `/api/tc-library/import/runs/{run_id}` | 작업 상세·행별 변경·결정. 내부 스냅샷/저널 제외 |
| POST | `/api/tc-library/import/runs/{run_id}/rollback` | 케이스·템플릿·분류·md 설정 복구. 이후 편집 시 409 `SUITE_CHANGED` |
| GET | `/api/tc-library/{suite}/tree` | 시트 › 대분류 › 중분류 › 소분류 › 제목 트리와 가지별 집계 |
| GET | `/api/tc-library/{suite}` | 케이스 목록. 쿼리: `sheet path status execution_result(빈 값=미실행) priority source invalid q offset limit` |
| POST | `/api/tc-library/{suite}/cases` | 케이스 추가 (`after`로 위치 지정), 201 |
| GET · PATCH · DELETE | `/api/tc-library/{suite}/cases/{case_id}` | 조회 · 부분 수정 `{rev, …}` · 소프트 삭제 `?rev=` |
| POST | `/api/tc-library/{suite}/cases/{case_id}/duplicate` · `/restore` · `/revert` | 복제 · 삭제 복원 · 이력 되돌리기 `{history_id, rev}` |
| GET | `/api/tc-library/{suite}/cases/{case_id}/history` | 변경 이력 (최신 먼저) |
| POST | `/api/tc-library/{suite}/bulk` | `{items:[{case_id,rev}], op:"set"|"delete", field, value}` → `{updated|deleted, conflicts}` |
| POST | `/api/tc-library/{suite}/move` | `{items, sheet, path, feature?}` → `{moved, conflicts}` |
| POST | `/api/tc-library/{suite}/export/xlsx` | `{scope, sheets?, case_ids?, history_note}` → `{export_id, filename, checks, count}` |
| GET | `/api/tc-library/exports/{export_id}/download` | 내보낸 xlsx 내려받기 |

저장 위치: `state/tc_library/{suite}/` (`cases.json`, `history.jsonl`, `template.xlsx`, `template_profile.json`), 작업 공간 `state/tc_library/_uploads/`, `_exports/`.

화면은 파일 분석 → 변경 미리보기 → 반영 순서를 사용한다. 미리보기 행은 `new/updated/same/conflict/error`이며 충돌은 skip 또는 overwrite, 오류는 skip 결정을 요구한다. 같은 이름의 시트를 여러 파일에서 한 작업에 선택하면 409 `DUPLICATE_SHEET`. 반영 전 업로드·스위트 변경은 409 `SOURCE_CHANGED`/`SUITE_CHANGED`로 거부한다. 가져오기 작업·복구 자료는 `state/tc_library/_import_runs/`에 저장한다. 기존 단일 파일 API는 서버가 계획을 만든 뒤 반영하는 호환 경로를 유지한다.

매핑 필드: `source_tc_id,feature,steps,expected,precondition,l1,l2,l3,priority,tags,note`. 제목·Step·Expected는 필수이며 열은 A~XFD, 헤더 행은 1~1048576이다. 프로필은 기존 `state/import_profiles.json`의 `mappings` 형식으로 저장하여 `/api/import/profiles`와 공유한다. 잘못된 프로필은 400 `INVALID_PROFILE`, 잘못된 JSON은 400 `INVALID_JSON`, 이름 중복은 409 `PROFILE_EXISTS`, 없는 프로필은 404 `PROFILE_NOT_FOUND`.

md 이력은 기존 `state/import_sessions`·`import_snapshots`를 사용한다. 손상된 목록 항목은 `errors`로 알리고 나머지를 반환한다. `/api/import/*` 및 `/api/import/runs/{run_id}/skipped.csv`는 유지한다. `/import-studio`는 `/tc-studio`로 이동한다.



#### 생성·검토 (`routes_tc_authoring.py`)

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/tc-library/sources` | 소스 묶음 생성 |
| GET | `/api/tc-library/sources/{bundle}` | 묶음 매니페스트 |
| POST | `/api/tc-library/sources/{bundle}/file?filename=` | 파일 추가 (.pdf .docx .md .txt, 25MB, PDF 200쪽) |
| POST | `/api/tc-library/sources/{bundle}/paste` | 붙여넣기 추가 `{text}` (1MB) |
| DELETE | `/api/tc-library/sources/{bundle}/{source_id}` | 소스 제거 |
| GET | `/api/tc-library/sources/{bundle}/excerpt?ref=` | 출처 섹션 발췌 |
| GET · PUT | `/api/tc-library/profiles` · `/api/tc-library/profiles/{name}` | 작성 프로필 |
| POST | `/api/tc-library/{suite}/jobs` | 생성 작업 시작 (동시 1건, 409 `JOB_RUNNING`, 503 `CLAUDE_NOT_FOUND`) |
| GET | `/api/tc-library/jobs/{job_id}` | 작업 상태 · 로그 끝 40줄 · 버린 초안 |
| POST | `/api/tc-library/jobs/{job_id}/cancel` | 작업 취소 |
| GET | `/api/tc-library/{suite}/coverage?sheet&path&profile` | 기능별 커버리지 갭 |
| POST | `/api/tc-library/{suite}/cases/{id}/resolve-duplicate` | 중복 처리 `{rev, action: update|skip|add, target_case_id, target_rev}` |
| GET | `/api/tc-library/import/mapping-profiles` | `{profiles:[{id,name,mapping:{header_row,columns},columns}]}`. 기존 `columns` 필드 유지 |
| POST | `/api/tc-library/import/mapping-profiles` | `{name,mapping}` → 201 `{profile}` |
| PUT | `/api/tc-library/import/mapping-profiles/{id}` | `{name,mapping}` → `{profile}` |
| DELETE | `/api/tc-library/import/mapping-profiles/{id}` | `{deleted:id}` |
| GET | `/api/tc-library/import/md-runs` | 기존 Excel→md 및 TC→md 작업 목록 `{runs,errors}` |
| GET | `/api/tc-library/import/md-runs/{run_id}` | 공개 작업 상세·행별 before/after·`skipped_csv_url` |
| POST | `/api/tc-library/import/md-runs/{run_id}/rollback` | 기존 md 스냅샷 복구. TC 작업이면 해당 스위트의 내보내기 기록도 복구 |

생성 작업은 `claude -p --restricted --strict-mcp-config --tools "" --permission-mode dontAsk --no-session-persistence --output-format json --json-schema …`로 저장소 밖 임시 폴더에서 실행한다. 환경변수: `TCS_CLAUDE_BIN`(CLI 경로), `TCS_CLAUDE_MODEL`(모델), `TCS_CHUNK_TIMEOUT`(섹션당 초, 기본 300). 작업 기록은 `state/tc_library/_jobs/{job_id}/`.

#### 원격 소스·출처 추적 (`routes_tc_connectors.py`)

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/tc-library/credentials` | 연결 상태 (토큰 없음) |
| PUT | `/api/tc-library/credentials/{confluence\|figma}` | 저장 → 연결 상태 |
| POST | `/api/tc-library/sources/{bundle}/url` | `{url}` → 201 `{source}` |
| POST | `/api/tc-library/sources/{bundle}/confluence` | `{url, children}` → 201 `{sources}` |
| POST | `/api/tc-library/sources/{bundle}/figma` | `{url}` → 201 `{source}` |
| GET | `/api/tc-library/sources/{bundle}/assets/{name}` | Figma 프레임 PNG |
| GET | `/api/tc-library/source-diff?ref=` | 차이 |
| POST | `/api/tc-library/{suite}/source-changes/scan` | 원격 버전 확인 → 표시 |
| GET | `/api/tc-library/{suite}/source-changes` | 표시된 변경 (원격 호출 없음) |
| POST | `/api/tc-library/{suite}/cases/{id}/ack-source` | 확인 완료 |

원격 요청은 `_tc_fetch.fetch()`만 거친다: https·호스트 허용 목록·내부망 차단·리다이렉트 재검사(최대 3)·15초·20MB. 자격증명 파일 `config/confluence_config.json`, `config/figma_config.json`(git 제외), 환경변수 `CONFLUENCE_BASE_URL` `CONFLUENCE_EMAIL` `CONFLUENCE_TOKEN` `FIGMA_TOKEN`이 우선한다.

#### md 내보내기 (`routes_tc_md.py`)

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/tc-library/{suite}/export/md/eligibility` | 퍼널·가지 매핑·제외·드리프트 |
| PUT | `/api/tc-library/{suite}/md-groups` | `{path, group, code}` |
| POST | `/api/tc-library/{suite}/export/md` | 미리보기 → `{run_id, summary, rows[{tc_id, case_id, status, reason, reason_code, file, excluded, before, after}]}` |
| POST | `/api/tc-library/{suite}/md-exports/{run_id}/commit` | `{skip: [tc_id]}` → Import Studio 커밋 결과 |
| POST | `/api/tc-library/{suite}/md-exports/{run_id}/rollback` | 롤백 |

`ImportRunError`는 409 `{code}`로 반환한다. 미리보기·반영·롤백은 기존 Import Studio 커밋 엔진을 사용한다.

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
.venv/bin/python agents/dashboard/serve.py --host 0.0.0.0 --port 8800
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
