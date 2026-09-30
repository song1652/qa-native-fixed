# 문서 안내

사용 목적에 맞는 문서부터 읽으세요. **TC 스튜디오를 처음 사용한다면 [사용자 설명서](tc-studio/TC_AUTHORING_USER_GUIDE.md)부터 시작합니다.**

## TC 스튜디오

TC 작성·검토·내보내기 기능의 문서와 자료는 [`tc-studio/`](tc-studio/)에 모았습니다.

| 목적 | 문서 |
|---|---|
| 처음 사용하기, 기획 입력, TC 작성·수정·검토, Excel/Markdown 내보내기 | [사용자 설명서](tc-studio/TC_AUTHORING_USER_GUIDE.md) |
| 빈 양식과 연습 자료 찾기 | [TC 스튜디오 문서 안내](tc-studio/README.md#예제와-화면-자료) |
| 완료된 기능과 검증 범위 확인 | [구현 보고](tc-studio/TC_AUTHORING_IMPLEMENTATION_REPORT.md) |
| 설계·개발 계획 확인 | [TC 스튜디오 문서 안내](tc-studio/README.md#개발-참고-문서) |

## QA 파이프라인 사용과 개발 참고

| 문서 | 언제 읽는가 |
|---|---|
| [프로젝트 README](../README.md) | 프로젝트 설치와 시작 방법 |
| [테스트케이스 작성 가이드](TEST_CASE_GUIDE.md) | 파이프라인용 TC 문서의 작성 규칙 |
| [스크립트 실행 가이드](SCRIPTS_GUIDE.md) | Python 스크립트의 역할과 실행 방법 |
| [API·CLI 레퍼런스](API_REFERENCE.md) | 명령 옵션과 대시보드 API 확인 |
| [프로젝트 아키텍처](PROJECT_OVERVIEW.md) | 시스템 구성과 설계 의도 파악 |
| [프롬프트 레퍼런스](PROMPTS_REFERENCE.md) | 프롬프트 템플릿의 입출력 확인 |
| [디렉토리 구조](DIRECTORY.md) | 저장소 구조 확인. 자동 생성 문서 |

## 에이전트 운영 지침

| 문서 | 언제 읽는가 |
|---|---|
| [저장소 공통 지침](../CLAUDE.md) | 저장소에서 작업하기 전 필요한 행동 원칙·절대 규칙 확인 |
| [힐링 가이드](HEALING_GUIDE.md) | 실패 진단과 수정 절차 확인 |
| [파이프라인 상태](PIPELINE_STATE.md) | 상태 파일 스키마와 전이 규칙 확인 |
| [팀 토론 절차](TEAM_DISCUSSION.md) | 팀 토론 기능을 진행할 때 |

## 폴더 구성과 관리 기준

```text
doc/
├─ README.md                 문서 전체 안내
├─ *.md                      QA 파이프라인 참고·운영 문서
└─ tc-studio/
   ├─ README.md              TC 스튜디오 문서 안내
   ├─ TC_AUTHORING_*.md      사용자 설명서·설계·구현 기록
   ├─ plans/                 완료된 Phase 1~4 구현 계획
   ├─ templates/             빈 Excel 양식·연습용 기획 정보
   └─ images/                사용자 설명서의 실제 화면 캡처
```

- 새 기능의 문서는 기능 폴더에 모으고 이 안내에 연결합니다.
- 사용자 설명서는 현재 사용 방법을 설명합니다. 구현 보고는 수행한 작업과 확인 범위를 기록합니다.
- 개발 계획과 초기 설계는 삭제하지 않고 참고 기록으로 보존합니다. 완료된 계획을 현재 해야 할 작업으로 오해하지 않도록 상태를 안내합니다.
- 문서를 이동할 때 내부 링크, 프로젝트 README, 명령에 적힌 문서 경로를 함께 수정합니다.
- `DIRECTORY.md`는 자동 생성 문서입니다. 상세 문서의 탐색 시작점은 이 `README.md`를 사용합니다.
