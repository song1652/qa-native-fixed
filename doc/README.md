# 문서 안내

문서는 **무엇을 하기 위해 읽는가**에 따라 분류합니다. 처음 사용하는 사람은 사용 매뉴얼부터 읽고, 개발자는 API·상태·프롬프트 레퍼런스와 저장소 공통 지침을 참고하세요.

## 어디부터 읽으면 되나요?

| 목적 | 시작 문서 |
|---|---|
| 프로젝트 설치·시작 | [프로젝트 README](../README.md) |
| 최신 웹 화면과 리포트 사용법 | [웹 QA 대시보드 사용자 가이드](guides/USER_GUIDE.html) |
| 웹에서 TC 작성·수정·검토 후 내보내기 | [TC 스튜디오 사용자 설명서](guides/tc-studio/TC_AUTHORING_USER_GUIDE.html) |
| Markdown TC를 직접 작성 | [TC 작성 가이드](guides/TEST_CASE_GUIDE.html) |
| 스크립트로 QA 파이프라인 사용 | [스크립트 사용 매뉴얼](guides/SCRIPTS_GUIDE.html) |
| API·상태·프롬프트 구조 확인 | [레퍼런스](#레퍼런스-reference) |
| 에이전트 운영·실패 수정·팀 토론 | [운영 지침](#운영-지침-operations) |

## 사용 매뉴얼: guides

| 문서 | 설명 |
|---|---|
| [웹 QA 대시보드 사용자 가이드](guides/USER_GUIDE.html) | 최신 밝은 테마 화면 10장으로 메뉴·실행·리포트 사용법 안내 |
| [TC 스튜디오 사용자 설명서](guides/tc-studio/TC_AUTHORING_USER_GUIDE.html) | 기획 입력 → 초안 생성/직접 작성 → 수정/검토 → Excel·Markdown 내보내기. 테스트 실행 절차는 포함하지 않음 |
| [TC 작성 가이드](guides/TEST_CASE_GUIDE.html) | Markdown 파일 형식, 필수 항목, 작성 예시와 체크리스트 |
| [스크립트 사용 매뉴얼](guides/SCRIPTS_GUIDE.html) | 프로그램 실행 순서, 주요 스크립트의 역할, 설정·로그 위치 |
| [빈 Excel 양식](guides/tc-studio/templates/TC_빈양식.xlsx) | 작성 내용이 없는 시작용 양식 |
| [회원 등록 기획 예시](guides/tc-studio/templates/회원등록_기획예시.md) | 따라 하기용 가상 요구사항 |

## 레퍼런스: reference

| 문서 | 설명 |
|---|---|
| [API·CLI](reference/API_REFERENCE.md) | 인자·엔드포인트·요청/응답 참고 |
| [파이프라인 상태](reference/PIPELINE_STATE.md) | 상태 스키마와 전이 규칙. 레지스트리가 단일 기준 |
| [프롬프트](reference/PROMPTS_REFERENCE.md) | 컨텍스트 입력과 프롬프트 템플릿 |
| [디렉토리 구조](reference/DIRECTORY.md) | 자동 생성되는 저장소 구조. 상세 문서 목록도 포함 |

## 운영 지침: operations

| 문서 | 설명 |
|---|---|
| [힐링 지침](operations/HEALING_GUIDE.md) | 에이전트가 실패를 진단하고 수정할 때 따르는 절차 |
| [팀 토론 지침](operations/TEAM_DISCUSSION.md) | 대시보드 토론 기록·승인·후속 처리 절차 |
| [저장소 공통 지침](../CLAUDE.md) | 작업에 적용되는 행동 원칙과 절대 규칙 |

## 관리 기준

```text
doc/
├─ README.md                 전체 문서 탐색 시작점
├─ guides/                   HTML 가이드·Markdown 수정 원본·예제
├─ images/                   현재 화면 캡처·촬영 기준
├─ reference/                API·스키마·프롬프트·자동 생성 구조
└─ operations/               에이전트 운영 절차
```

- 사용 방법과 최신 화면은 `guides`, 정확한 계약은 `reference`, 운영 절차는 `operations`에서 관리합니다.
- 초기 PRD·디자인 목업·완료된 개발 계획·인수인계 문서는 정리했습니다. 이전 내용이 필요하면 Git 이력을 확인하세요.
- 같은 API 표를 여러 문서에 복제하지 않고 레퍼런스로 연결합니다.
- 문서 이동 시 링크·프롬프트·자동 생성기·문서 동기화 테스트를 함께 갱신합니다.
- Markdown과 예제 파일이 실행할 명령을 제시할 때는 프로젝트 루트 기준임을 명시합니다.

## HTML 가이드 열기

[사용자 가이드](guides/USER_GUIDE.html)를 브라우저로 엽니다. 왼쪽 목차에서 장을 선택하고, 이미지를 누르면 원본 크기로 볼 수 있습니다. 좁은 화면에서는 **목차 열기**를 사용하고, 인쇄는 브라우저의 기본 인쇄 기능을 사용합니다.

로컬 웹으로 보려면 프로젝트 루트에서 다음 명령을 실행합니다.

```sh
python3 -m http.server 8768 --bind 127.0.0.1 --directory .
```

브라우저 주소는 **http://localhost:8768/doc/guides/USER_GUIDE.html**입니다. QA 대시보드는 별도로 **8766**에서 실행합니다.

## 가이드와 이미지 갱신 규칙

1. 사용자에게 제공하는 읽기용 문서는 **HTML**입니다. 내용 수정은 같은 폴더의 **Markdown 원본**에서 합니다. `USER_GUIDE.html`의 원본은 `DASHBOARD_USER_GUIDE.md`입니다.
2. 내용 수정 후 프로젝트 루트에서 아래 명령으로 HTML을 갱신합니다. 생성된 HTML을 직접 고치지 않습니다.
3. 화면·버튼·문구가 바뀌면 해당 가이드와 실제 화면 캡처를 함께 갱신합니다. 캡처는 `doc/images/`에 두고 [촬영 기준](images/README.md)에 날짜·크기·출처·예시 상태 여부를 기록합니다.
4. Markdown 원본·HTML·필요한 이미지·촬영 기록을 같은 커밋에 포함합니다. API·운영 문서는 기존 Markdown을 유지합니다.
5. 업데이트 확인은 `--check`와 문서 테스트로 수행합니다. 목차·이미지·모바일 화면은 브라우저로 확인합니다.

```sh
# 최초 1회: 문서 생성 도구 설치 (대시보드 실행에는 불필요)
python3 -m pip install -r requirements-docs.txt

# 원본 변경 후 HTML 갱신
python3 scripts/build_user_guides.py

# 갱신 누락 확인: 불일치가 있으면 종료코드 1
python3 scripts/build_user_guides.py --check

# 문서 목록 갱신과 링크·목차·레지스트리 확인
python3 scripts/update_directory.py
python3 -m pytest tests/unit/core/test_html_guides.py tests/unit/core/test_documentation_index.py tests/unit/core/test_doc_registry_sync.py -q -W ignore -p no:cacheprovider
```
