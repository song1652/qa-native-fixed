# TC 스튜디오 문서 안내

## 사용자 문서

**[TC 스튜디오 사용자 설명서](TC_AUTHORING_USER_GUIDE.md)** — 처음 사용하는 사람을 위한 기획 정보 입력, LLM 초안 생성, 직접 작성·수정, 검토, Excel·Markdown 내보내기 안내입니다. 처음에는 1~5장을 순서대로 따라 하세요.

이 설명서의 범위는 내보내기까지입니다. 테스트 실행·결과 보고 절차는 포함하지 않습니다.

## 예제와 화면 자료

| 자료 | 용도 |
|---|---|
| [빈 TC Excel 양식](templates/TC_빈양식.xlsx) | TC 내용이 없는 시작용 양식 |
| [회원 등록 기획 예시](templates/회원등록_기획예시.md) | 기획 입력과 초안 생성을 연습하는 가상의 요구사항 |
| [화면 캡처](images/tc-studio-user-guide/) | 사용자 설명서에 포함된 실제 화면 4개 |

## 개발 참고 문서

Phase 1~4 구현은 완료되었습니다. 실제 구현 결과와 계정 연동 등 확인하지 못한 범위는 **구현 보고**를 기준으로 확인합니다. 초기 설계와 계획에는 후속 개선 전의 내용이 남아 있을 수 있습니다.

| 문서 | 역할 |
|---|---|
| [구현 보고](TC_AUTHORING_IMPLEMENTATION_REPORT.md) | Phase별 결과, 테스트 수, 실제 사용 검증, 후속 수정 기록 |
| [로드맵](TC_AUTHORING_ROADMAP.md) | Phase 구성과 작업 ID, 완료 상태 |
| [PRD](TC_AUTHORING_PRD.md) | 최초 요구사항과 설계 참고 |
| [요소별 동작 명세](TC_AUTHORING_ELEMENT_SPEC.md) | 화면 요소와 API의 설계 참고 |
| [개발 인수인계](TC_AUTHORING_HANDOFF.md) | 최초 구현에 사용한 작업 절차와 보고 형식 |
| [화면 목업](../../design-previews/tc-authoring-studio.html) | 초기 화면 설계 |

### 완료된 구현 계획

| Phase | 계획 | 범위 |
|---|---|---|
| 1 | [Phase 1](plans/2026-09-29-tc-authoring-phase1.md) | 라이브러리·Excel 가져오기/내보내기 |
| 2 | [Phase 2](plans/2026-09-30-tc-authoring-phase2.md) | 파일 소스·초안 생성·검토 |
| 3 | [Phase 3](plans/2026-09-30-tc-authoring-phase3.md) | Confluence·Figma·URL·출처 추적 |
| 4 | [Phase 4](plans/2026-09-30-tc-authoring-phase4.md) | Markdown 내보내기 |

계획 안의 코드는 당시 구현을 위한 기록입니다. 현재 사용법을 찾을 때는 사용자 설명서를 읽으세요.

[전체 문서 안내로 돌아가기](../README.md)
