# 문서 안내

문서는 **무엇을 하기 위해 읽는가**에 따라 분류합니다. 처음 사용하는 사람은 사용 매뉴얼부터 읽고, 개발자는 API·상태·프롬프트 레퍼런스와 저장소 공통 지침을 참고하세요.

## 어디부터 읽으면 되나요?

| 목적 | 시작 문서 |
|---|---|
| 프로젝트 설치·시작 | [프로젝트 README](../README.md) |
| 최신 웹 화면과 리포트 사용법 | [웹 QA 대시보드 사용자 가이드](guides/DASHBOARD_USER_GUIDE.md) |
| 웹에서 TC 작성·수정·검토 후 내보내기 | [TC 스튜디오 사용자 설명서](guides/tc-studio/TC_AUTHORING_USER_GUIDE.md) |
| Markdown TC를 직접 작성 | [TC 작성 가이드](guides/TEST_CASE_GUIDE.md) |
| 스크립트로 QA 파이프라인 사용 | [스크립트 사용 매뉴얼](guides/SCRIPTS_GUIDE.md) |
| API·상태·프롬프트 구조 확인 | [레퍼런스](#레퍼런스-reference) |
| 에이전트 운영·실패 수정·팀 토론 | [운영 지침](#운영-지침-operations) |

## 사용 매뉴얼: guides

| 문서 | 설명 |
|---|---|
| [웹 QA 대시보드 사용자 가이드](guides/DASHBOARD_USER_GUIDE.md) | 최신 밝은 테마 화면 10장으로 메뉴·실행·리포트 사용법 안내 |
| [TC 스튜디오 사용자 설명서](guides/tc-studio/TC_AUTHORING_USER_GUIDE.md) | 기획 입력 → 초안 생성/직접 작성 → 수정/검토 → Excel·Markdown 내보내기. 테스트 실행 절차는 포함하지 않음 |
| [TC 작성 가이드](guides/TEST_CASE_GUIDE.md) | Markdown 파일 형식, 필수 항목, 작성 예시와 체크리스트 |
| [스크립트 사용 매뉴얼](guides/SCRIPTS_GUIDE.md) | 프로그램 실행 순서, 주요 스크립트의 역할, 설정·로그 위치 |
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
├─ guides/                   사용 방법·작성 매뉴얼·예제·화면
├─ reference/                API·스키마·프롬프트·자동 생성 구조
└─ operations/               에이전트 운영 절차
```

- 사용 방법과 최신 화면은 `guides`, 정확한 계약은 `reference`, 운영 절차는 `operations`에서 관리합니다.
- 초기 PRD·디자인 목업·완료된 개발 계획·인수인계 문서는 정리했습니다. 이전 내용이 필요하면 Git 이력을 확인하세요.
- 같은 API 표를 여러 문서에 복제하지 않고 레퍼런스로 연결합니다.
- 문서 이동 시 링크·프롬프트·자동 생성기·문서 동기화 테스트를 함께 갱신합니다.
- Markdown과 예제 파일이 실행할 명령을 제시할 때는 프로젝트 루트 기준임을 명시합니다.
