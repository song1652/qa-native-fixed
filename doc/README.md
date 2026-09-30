# 문서 안내

문서는 **무엇을 하기 위해 읽는가**에 따라 분류합니다. 처음 사용하는 사람은 사용 매뉴얼부터 읽고, 개발자는 설계와 레퍼런스를 필요한 만큼 참고하세요.

## 어디부터 읽으면 되나요?

| 목적 | 시작 문서 |
|---|---|
| 프로젝트 설치·시작 | [프로젝트 README](../README.md) |
| 웹에서 TC 작성·수정·검토 후 내보내기 | [TC 스튜디오 사용자 설명서](guides/tc-studio/TC_AUTHORING_USER_GUIDE.md) |
| Markdown TC를 직접 작성 | [TC 작성 가이드](guides/TEST_CASE_GUIDE.md) |
| 스크립트로 QA 파이프라인 사용 | [스크립트 사용 매뉴얼](guides/SCRIPTS_GUIDE.md) |
| 개발 중 요구사항·설계 확인 | [설계 문서](#설계-design) |
| API·상태·프롬프트 구조 확인 | [레퍼런스](#레퍼런스-reference) |
| 구현 경과와 검토 결과 확인 | [개발 기록](#개발-기록-development) |
| 에이전트 운영·실패 수정·팀 토론 | [운영 지침](#운영-지침-operations) |

## 사용 매뉴얼: guides

| 문서 | 설명 |
|---|---|
| [TC 스튜디오 사용자 설명서](guides/tc-studio/TC_AUTHORING_USER_GUIDE.md) | 기획 입력 → 초안 생성/직접 작성 → 수정/검토 → Excel·Markdown 내보내기. 테스트 실행 절차는 포함하지 않음 |
| [TC 작성 가이드](guides/TEST_CASE_GUIDE.md) | Markdown 파일 형식, 필수 항목, 작성 예시와 체크리스트 |
| [스크립트 사용 매뉴얼](guides/SCRIPTS_GUIDE.md) | 프로그램 실행 순서, 주요 스크립트의 역할, 설정·로그 위치 |
| [빈 Excel 양식](guides/tc-studio/templates/TC_빈양식.xlsx) | 작성 내용이 없는 시작용 양식 |
| [회원 등록 기획 예시](guides/tc-studio/templates/회원등록_기획예시.md) | 따라 하기용 가상 요구사항 |

## 설계: design

| 문서 | 설명 |
|---|---|
| [프로젝트 아키텍처](design/PROJECT_OVERVIEW.md) | 시스템 구성·설계 원칙·데이터 흐름 |
| [TC 스튜디오 PRD](design/tc-studio/TC_AUTHORING_PRD.md) | 기능 요구사항과 최초 설계. 현재 사용법은 사용자 설명서를 참고 |
| [TC 스튜디오 요소 명세](design/tc-studio/TC_AUTHORING_ELEMENT_SPEC.md) | 화면 요소·API의 설계 참고. 초기 제안과 실제 구현이 다를 수 있음 |

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

## 개발 기록: development

| 문서 | 설명 |
|---|---|
| [TC 스튜디오 구현 보고](development/tc-studio/TC_AUTHORING_IMPLEMENTATION_REPORT.md) | 완료된 작업, 확인 결과, 제한, 후속 개선 |
| [TC 스튜디오 로드맵](development/tc-studio/TC_AUTHORING_ROADMAP.md) | Phase 구성과 완료 상태 |
| [TC 스튜디오 개발 인수인계](development/tc-studio/TC_AUTHORING_HANDOFF.md) | 최초 구현 시 사용한 절차와 보고 형식 |
| [Phase 1](development/tc-studio/plans/2026-09-29-tc-authoring-phase1.md) | 완료된 라이브러리·Excel 구현 계획 |
| [Phase 2](development/tc-studio/plans/2026-09-30-tc-authoring-phase2.md) | 완료된 소스·생성·검토 구현 계획 |
| [Phase 3](development/tc-studio/plans/2026-09-30-tc-authoring-phase3.md) | 완료된 원격 소스·출처 추적 구현 계획 |
| [Phase 4](development/tc-studio/plans/2026-09-30-tc-authoring-phase4.md) | 완료된 Markdown 내보내기 구현 계획 |
| [Import Studio 통합 검토](development/tc-studio/IMPORT_STUDIO_INTEGRATION_REVIEW.md) | 에이전트 논의 결과와 TC 스튜디오 통합 선행 조건. 미구현 제안 |
| [문서 정리 기록](development/DOCUMENTATION_REVIEW.md) | 이번 분류 기준·중복 처리·확인한 오래된 설명 |

TC 스튜디오 관련 자료만 찾으려면 [기능별 안내](tc-studio/README.md)를 사용하세요.

## 관리 기준

```text
doc/
├─ README.md                 전체 문서 탐색 시작점
├─ guides/                   사용 방법·작성 매뉴얼·예제·화면
├─ design/                   요구사항(PRD)·아키텍처·화면 설계
├─ reference/                API·스키마·프롬프트·자동 생성 구조
├─ operations/               에이전트 운영 절차
├─ development/              구현 보고·완료된 계획·검토 기록
└─ tc-studio/README.md        TC 스튜디오 관련 문서 바로가기
```

- 사용 방법은 `guides`, 요구사항과 의도는 `design`, 정확한 계약은 `reference`에 작성합니다.
- 작업 결과와 과거 계획은 `development`에 둡니다. 완료된 계획을 현재 실행 지시로 사용하지 마세요.
- 설계의 ‘Draft’ 상태와 구현 완료는 별개입니다. 실제 확인 범위는 구현 보고를 참고합니다.
- 같은 API 표를 여러 문서에 복제하지 않고 레퍼런스로 연결합니다.
- 문서 이동 시 링크·프롬프트·자동 생성기·문서 동기화 테스트를 함께 갱신합니다.
- Markdown과 예제 파일이 실행할 명령을 제시할 때는 프로젝트 루트 기준임을 명시합니다.
