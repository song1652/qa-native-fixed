# 문서 정리 기록

> 2026-09-30 · 문서 정리 범위: doc 전체의 사용 매뉴얼, 설계, 레퍼런스, 운영 지침, 개발 기록.

## 정리 기준

문서를 읽고 독자와 목적을 기준으로 분류했습니다. 처음에는 TC 스튜디오 자료만 모았으나, 전체 문서 정리가 요청 범위임을 확인하고 분류를 확장했습니다.

| 기존 문서 | 새 분류 | 판단 |
|---|---|---|
| TEST_CASE_GUIDE | guides | 사용자가 Markdown TC를 작성하는 매뉴얼 |
| SCRIPTS_GUIDE | guides | 실행 절차·스크립트 역할 안내 |
| TC_AUTHORING_USER_GUIDE | guides/tc-studio | 웹 사용자의 작성·내보내기 매뉴얼 |
| PROJECT_OVERVIEW | design | 시스템 설계·아키텍처 설명 |
| TC_AUTHORING_PRD·ELEMENT_SPEC | design/tc-studio | 요구사항과 초기 화면 설계 |
| API_REFERENCE | reference | API·CLI 계약 |
| PIPELINE_STATE | reference | 상태 스키마·전이 규칙 |
| PROMPTS_REFERENCE | reference | 컨텍스트·프롬프트 구조 |
| DIRECTORY | reference | 자동 생성 구조 문서 |
| HEALING_GUIDE·TEAM_DISCUSSION | operations | 에이전트 운영 절차 |
| TC_AUTHORING_HANDOFF·ROADMAP·IMPLEMENTATION_REPORT·plans | development/tc-studio | 개발 절차와 완료된 작업의 기록 |

## 중복·혼동 처리

- SCRIPTS_GUIDE의 대시보드 API 목록은 API_REFERENCE와 중복되어 링크로 교체했습니다. 실행 순서와 역할 설명은 매뉴얼에 유지했습니다.
- API_REFERENCE의 CLI 요약은 인자를 찾기 위한 레퍼런스이며, 매뉴얼의 따라 하기 예제와 역할이 달라 유지했습니다.
- PRD·요소 명세는 현재 화면의 사용 매뉴얼과 구분하는 안내를 추가했습니다. 초기 설계 내용은 기록으로 보존합니다.
- ‘아직 코드 없음’으로 남았던 인수인계의 상태는 완료된 구현 보고를 안내하도록 수정했습니다.
- 전체 문서 목록은 doc/README.md 한 곳에서 관리하고 프로젝트 README는 그곳으로 연결합니다. 중복이던 TC 스튜디오 바로가기(doc/tc-studio/README.md)는 2026-10-01 삭제했습니다.

## 코드와 비교해 수정한 오래된 설명

- 테스트 데이터 위치: config/test_data.json 대신 test_data/{product}.json 및 load_test_data()의 프로덕트별 읽기 구조.
- Plan·코드 리뷰: 현재 02a/03a 컨텍스트에는 페르소나가 없으므로 체크리스트 방식으로 설명. 힐링·팀 토론은 별도.
- 반려 종료 코드: EXIT_REJECTED는 4이며 힐링 횟수 초과의 2와 구분.
- 05_execute의 워커 수: 자동 선택, 최대 4. 스크립트가 지원하지 않는 -n 인자 안내는 제거.
- TC 작성 가이드: UI 문구를 영어로 강제하지 않고 실제 표시 언어의 원문을 사용.
- 문서 종류와 독자를 각 주요 문서 앞에 표시하고 자료 링크를 새 위치에 맞췄습니다.

## 유지 관리

DIRECTORY 자동 생성기는 doc의 Markdown 목록을 읽어 표를 만듭니다. 고정된 옛 파일 목록으로 새 문서를 빠뜨리지 않도록 회귀 테스트를 추가했습니다. 기존 레지스트리 동기화 검사의 확인 내용은 유지하고 문서 경로만 갱신했습니다.

이 정리는 제품 기능 변경이나 모든 과거 설계의 재검증을 의미하지 않습니다. PRD·완료된 계획의 기록은 보존하며, 현재 사용 방법과 검증 범위를 찾는 경로를 명확히 합니다.
