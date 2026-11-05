# QA Automation Web 온보딩

새로 합류한 QA 팀원이 로컬 환경을 준비하고 첫 웹 테스트의 결과를 확인하기 위한 문서입니다. 모든 명령은 `run_qa.py`와 `requirements.txt`가 있는 **프로젝트 루트**에서 실행합니다.

이 저장소(`qa-native-fixed`)는 **Playwright 기반 웹 QA 도구**입니다. `qa-native-app`의 Android/iOS 앱 테스트 도구와 구분하며, 기본 대시보드 포트는 **8766**입니다. Appium이나 모바일 가상 기기는 필요하지 않습니다.

## 1. 준비물

- Python 3.12 이상, Node.js 18 이상
- 저장소 접근 권한과 테스트 대상 사이트 접근 환경
- 코드 생성·기획 초안 생성·LLM 복구를 사용할 경우 설치·로그인된 Claude Code CLI
- 계정이 필요한 테스트라면 테스트용 계정과 입력 데이터

```bash
python3 --version
node --version
npm --version
claude --version
```

Claude Code CLI가 없다면 [README의 설치 안내](README.md#설치)를 따릅니다. 대시보드를 실행할 컴퓨터에서 로그인해야 합니다. 이 프로젝트는 별도의 LLM API 키 대신 Claude Code CLI를 사용합니다.

## 2. 프로젝트 설치

```bash
python3 scripts/setup_env.py
source .venv/bin/activate
```

설치 스크립트는 `.venv` 생성, `requirements.txt` 설치, Playwright Chromium 설치, `test_data/*.example.json`의 실제 데이터 파일 복사를 수행합니다. 재실행해도 기존 테스트 데이터는 덮어쓰지 않습니다.

설치를 확인합니다.

```bash
python --version
python -m pip check
python -m playwright --version
```

다음에 새 터미널을 열 때도 프로젝트 루트에서 `source .venv/bin/activate`를 실행합니다.

## 3. 테스트 URL과 입력 데이터 설정

| 위치 | 준비할 내용 |
|---|---|
| `config/pages.json` | `testcases/`의 그룹 폴더명과 테스트 URL 매핑 |
| `testcases/{그룹}/tc_*.md` | 케이스별 수행 단계·기대 결과·데이터 키 |
| `test_data/{프로덕트}.json` | 실제 테스트 입력값 |
| `test_data/{프로덕트}.example.json` | 팀에 공유하는 데이터 구조 예시 |

먼저 대상 URL을 브라우저로 열어 접근 가능하고 TC가 설명하는 화면인지 확인합니다. 저장소에 있는 URL이나 예시 계정이 현재 환경에서 동작한다고 가정하지 않습니다.

`config/pages.json`은 그룹별 URL 문자열 또는 아래 형태의 객체를 지원합니다. 아래는 추가할 항목의 예시이며 기존 설정 전체를 덮어쓰지 않습니다.

```json
{
  "my_web": {
    "url": "https://example.com/login",
    "spa": false,
    "preconditions": [],
    "notes": "우리 팀의 웹 로그인 테스트"
  }
}
```

`my_web`은 `testcases/my_web/`과 대응합니다. URL과 그룹명은 실제 값으로 바꿉니다.

실제 데이터 파일은 Git에서 제외됩니다. 설치 시 복사된 파일의 빈 값을 채우고, 새 프로덕트는 `.example.json`과 실제 `.json`을 함께 준비합니다. 파일명이 프로덕트 키가 됩니다. 데이터 키·TC 작성 규칙은 [TC 작성 가이드](doc/guides/TEST_CASE_GUIDE.html)와 [테스트 데이터 안내](test_data/README.md)를 참고하세요. 계정·비밀번호·연결 토큰을 TC나 공유용 예시에 넣지 않습니다.

Confluence·Figma 기획 정보는 TC 스튜디오의 **연결 설정**에서 설정합니다. Jira 실패 보고는 선택 사항이므로 첫 실행을 위해 준비할 필요는 없습니다.

## 4. 대시보드 시작

```bash
.venv/bin/python agents/dashboard/serve.py
```

브라우저가 자동으로 열리지 않으면 <http://localhost:8766>으로 접속합니다. 서버는 기본 `127.0.0.1`에 바인딩합니다. 종료는 서버 터미널에서 `Ctrl+C`를 누릅니다.

| 화면 | 첫 작업 |
|---|---|
| TC 스튜디오 | Excel 가져오기 또는 기획 정보로 초안 작성·검토·내보내기 |
| 페이지 URL 관리 | 내보낸 TC 그룹의 URL 확인 |
| 단일 파이프라인 | 처음에는 한 URL·한 그룹으로 분석·생성·실행 |
| 병렬 파이프라인 | 첫 실행 확인 후 여러 그룹으로 확대 |
| 빠른 실행 | 이미 생성된 pytest 코드 재실행 |
| 리포트·실행 기록 | 완료 상태·오류·실패 증거 확인 |

화면별 상세 조작은 [웹 QA 대시보드 사용자 가이드](doc/guides/USER_GUIDE.html)를 참고하세요.

## 5. 첫 테스트 실행

### 팀의 테스트 대상 사용

1. **TC 스튜디오**에서 Excel을 가져오거나 **기획 정보 · 생성**으로 초안을 만듭니다.
2. 라이브러리에서 단계·기대 결과를 확인하고, 생성 초안은 검토·승인합니다.
3. **내보내기**에서 그룹을 매핑하고 변경 미리보기를 확인한 후 Markdown을 반영합니다. 결과는 `testcases/{그룹}/tc_*.md`에 저장됩니다.
4. **페이지 URL 관리**에서 해당 그룹의 URL과 로컬 테스트 데이터를 확인합니다.
5. **단일 파이프라인**에서 URL·TC를 선택해 실행합니다. 생성 코드는 `tests/generated/{그룹}/`에서 확인합니다.
6. **실행 기록**에서 완료 상태를 확인하고 **리포트**에서 케이스별 결과와 증거를 확인합니다.

빠른 실행 목록이 비어 있다면 먼저 파이프라인으로 코드를 생성해야 합니다. TC 작성과 내보내기의 상세 절차는 [TC 스튜디오 설명서](doc/guides/tc-studio/TC_AUTHORING_USER_GUIDE.html)에 있습니다.

### 외부 사이트 없이 로컬 예제로 시작

별도 터미널에서 저장소에 포함된 회원 등록 페이지를 실행합니다.

```bash
.venv/bin/python -m http.server 8877 --bind 127.0.0.1 --directory tests/fixtures/tc_studio_demo
```

<http://localhost:8877>에서 페이지를 확인합니다. TC 스튜디오에 `tests/fixtures/tc_studio_demo/PRD.md`를 올려 초안을 만들거나 기존 `testcases/tc_studio_demo/`를 확인해 사용할 수 있습니다. 그룹은 `tc_studio_demo`, URL은 `http://localhost:8877`로 맞춥니다. 테스트가 끝날 때까지 예제 서버를 켜 둡니다.

이 예제도 코드·초안 생성에는 Claude 로그인이 필요합니다. 기존 케이스의 기대 문구와 페이지가 다르면 실패할 수 있으므로 성공 건수만 보고 설치 여부를 판단하지 않습니다. [로컬 예제 안내](tests/fixtures/tc_studio_demo/README.md)를 참고하세요.

## 6. 결과 확인과 실행 중 주의할 점

- 실행은 한 작업씩 진행합니다. 메뉴 이동·브라우저 종료는 실행 취소가 아니며, 취소하려면 상단 **실행 중단**을 사용합니다.
- CLI가 백그라운드 작업을 시작한 경우 터미널 프롬프트가 돌아와도 완료된 것이 아닙니다. 실행 기록의 시각·완료 상태·건수를 확인합니다.
- 서버 재시작 후 살아 있는 작업은 추적하지만 남은 단계를 자동으로 새로 시작하지 않습니다.
- 자동 복구는 요소 오류만 대상으로 합니다. 기대 결과·계정·연결 문제는 원인을 먼저 확인합니다. 복구 검증 실패 시 원본을 복원하고 추가 실행을 멈춥니다.
- 실행 시작 전 실패·시간 초과·중단은 HTML 리포트가 없을 수 있습니다. 실행 기록과 오류 알림을 함께 확인합니다.

| 경로 | 내용 |
|---|---|
| `tests/reports/` | HTML 리포트 |
| `tests/screenshots/` | 스크린샷과 케이스별 메타데이터 |
| `tests/videos/` | 실행 영상 |
| `tests/traces/` | 실패 Playwright Trace |
| `state/` · `logs/` | 실행 상태·결과·진행 로그 |

Trace는 `npx playwright show-trace <파일>.zip`으로 엽니다. 실행 산출물 중 일부는 현재 저장소에서 추적하므로 커밋 전에 `git status`로 확인합니다. 세부 복구 정책은 [복구 지침](doc/operations/HEALING_GUIDE.md)을 따릅니다.

## 7. 개발 참여 시 구조와 검증

대시보드 진입점은 `agents/dashboard/serve.py`, API 처리는 `agents/dashboard/routes_*.py`, 화면 자산은 `agents/dashboard/static/`에 있습니다. `run_qa.py`·`run_qa_parallel.py`는 실행 진입점이고, `scripts/`는 단계별 처리와 공통 라이브러리, `parallel/`은 병렬 실행을 담당합니다. 상태 전이의 기준은 `scripts/_pipeline_registry.py`입니다. 전체 구조는 [디렉토리 안내](doc/reference/DIRECTORY.md)를 참고하세요.

저장소 자체 회귀 테스트는 실제 사이트를 조작하는 생성 테스트와 구분해 실행합니다.

```bash
.venv/bin/python -m pytest tests/unit -q
```

문서 수정 후에는 아래 검증을 수행합니다. HTML 가이드 원본을 수정했다면 `scripts/build_user_guides.py`로 생성본도 갱신합니다.

```bash
.venv/bin/python scripts/build_user_guides.py --check
.venv/bin/python -m pytest tests/unit/core/test_html_guides.py tests/unit/core/test_documentation_index.py tests/unit/core/test_doc_registry_sync.py -q
```

문서 생성 의존성이 없으면 `requirements-docs.txt`를 설치합니다. 문서·이미지 갱신 규칙은 [문서 안내](doc/README.md#가이드와-이미지-갱신-규칙), 에이전트 작업 규칙은 [CLAUDE.md](CLAUDE.md)를 확인합니다.

## 8. 문제 해결

| 증상 | 확인·조치 |
|---|---|
| Python 모듈을 찾지 못함 | `.venv`를 활성화하고 설치 스크립트를 다시 실행합니다. |
| Chromium 실행 파일이 없음 | `.venv/bin/python -m playwright install chromium`을 실행합니다. |
| Claude 명령 없음·로그인 오류 | 서버를 실행한 환경의 `claude --version`과 로그인 상태를 확인합니다. |
| DOM 분석 실패 | URL·네트워크·접근 권한과 실제 페이지를 확인합니다. |
| 빠른 실행 목록이 비어 있음 | 파이프라인의 코드 생성 완료 여부와 `tests/generated/`를 확인합니다. |
| `KeyError`·데이터 파일 없음 | 실제 `test_data/{프로덕트}.json`과 케이스가 참조하는 키를 확인합니다. |
| 로컬 예제 연결 실패 | 8877 포트의 예제 서버를 실행하고 URL 매핑을 확인합니다. |
| 실행이 멈춘 것처럼 보임 | 실행 상태·오류 알림·로그를 확인하고, 중단 후 정리가 끝나기 전에 중복 실행하지 않습니다. |

CLI가 필요하면 [스크립트 사용 매뉴얼](doc/guides/SCRIPTS_GUIDE.html), 정확한 옵션·API는 [레퍼런스](doc/reference/API_REFERENCE.md)를 참고하세요.
