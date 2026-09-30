# TC Authoring Studio 개발 로드맵

> **독자**: 사람 + 구현 에이전트. PRD를 **작고 독립적으로 검증 가능한 작업**으로 쪼갠 전체 지도.
> 처음 개발을 맡는다면 [개발 인수인계](TC_AUTHORING_HANDOFF.md)부터 읽는다.
> 기준 문서: [PRD](../../design/tc-studio/TC_AUTHORING_PRD.md) · [요소별 동작 명세](../../design/tc-studio/TC_AUTHORING_ELEMENT_SPEC.md) · [목업](../../../design-previews/tc-authoring-studio.html)

## 상세 계획 (작업 단위 · 코드 · 테스트 포함)

| Phase | 문서 | 작업 | 새 테스트 | 검증 |
|---|---|---|---|---|
| 1 라이브러리 + 엑셀 왕복 | [phase1](plans/2026-09-29-tc-authoring-phase1.md) | B1~B10, W1~W4 | 40 | 사본 적용·전체 통과, 실제 야핏무브 926건 왕복 손실 0 · ✅ 완료 (2026-09-30) |
| 2 파일 소스 + 생성 + 검토 | [phase2](plans/2026-09-30-tc-authoring-phase2.md) | G1~G7, W5~W8 | 37 | 사본 적용·전체 통과, 실제 `claude` CLI 1회 생성 확인 · ✅ 완료 (2026-09-30) |
| 3 Confluence·Figma·URL + 출처 추적 | [phase3](plans/2026-09-30-tc-authoring-phase3.md) | C1~C5, W9~W11 | 22 | 사본 적용·전체 통과 (원격은 녹화 응답, 실제 계정 확인은 W11) · ✅ 구현·자동 테스트 완료 (2026-09-30), 실제 계정 미확인 |
| 4 md 내보내기 | [phase4](plans/2026-09-30-tc-authoring-phase4.md) | M1~M3, W12~W13 | 14 | 사본 적용·전체 3회 연속 통과, Import Studio 회귀 없음 · ✅ 완료 (2026-09-30) |
| 후속 Import 통합 | [통합 계획](plans/2026-09-30-import-integration.md) | I1~I6 | 최종 집계 예정 | 원본 값·프로필 CRUD·변경 확인·작업 복구·다중 파일·화면 통합 구현, 최종 검증은 구현 보고에 기록 |

모든 계획의 코드는 **저장소 사본에 순서대로 적용해 실행까지 확인한 코드**다(2026-09-29~30). 초기 네 Phase 기준으로 기존 677개 + TC 스튜디오 113개 = **790개**가 통과해야 한다.

---

## 1. 쪼개는 원칙

- **작업 1개 = 테스트 1묶음 + 커밋 1개.** 리뷰어가 이 작업만 따로 반려할 수 있는 크기로 자른다.
- **백엔드 먼저, 화면은 나중에.** 모델 → 저장소 → API → 화면 순서로 쌓는다.
- **Phase마다 쓸 수 있는 결과가 나온다.** Phase 1만 끝나도 "엑셀 TC를 웹에서 관리하고 다시 엑셀로 뽑는" 기능이 동작한다.
- **기존 코드 규칙을 따른다.** 상태 쓰기는 `update_state`, 경로는 `_paths`, 대시보드 라우트는 Mixin, 단위 테스트는 `tests/unit/`.

## 2. 전체 흐름과 의존 관계

```
Phase 1  라이브러리 + 엑셀 왕복
  B1 모델 → B2 템플릿 분석 → B3 엑셀 가져오기 → B4 저장소 → B5 트리·필터
  B6 엑셀 쓰기 → B7 무결성 검사 → B8~B10 API → W1 셸·라이브러리·상세 → W2 가져오기 → W3 내보내기 → W4 문서
        │
        ▼
Phase 2  파일 소스 + 생성 + 검토
  G1 저장소 확장 → G2 소스 번들 → G3 프로필·프롬프트 → G4 중복·커버리지 → G5 생성 실행기 → G6 직접 매핑 → G7 API
  W5 새로 생성 → W6 초안 검토 → W7 가져오기 직접 매핑 → W8 문서
        │
        ▼
Phase 3  원격 소스 + 출처 추적
  C1 안전한 수집기 → C2 자격증명 → C3 커넥터 → C4 출처 추적 → C5 API → W9 원격 소스 탭 → W10 변경 배너 → W11 문서·실계정
        │
        ▼
Phase 4  md 내보내기 (Phase 1만 있으면 개념상 가능하지만, 계획의 diff는 Phase 3 적용 상태 기준)
  M1 파이프라인 계약 정리 → M2 md 내보내기 → M3 API → W12 md 카드 → W13 문서·실제 파이프라인
```

## 3. 결정 사항 모음

각 결정의 근거는 해당 Phase 계획의 "결정" 표에 있다.

| # | 결정 | Phase |
|---|---|---|
| Z1 | 실행 결과 필드 1개 `execution_result` (`""` 미실행 / pass / fail / not_test / na). And·iOS가 다르면 fail > na > pass > not_test | 1 |
| Z2 | 케이스 API 경로에 스위트 포함: `/api/tc-library/{suite}/cases/{case_id}` | 1 |
| Z3 | 엑셀 업로드는 원본 바이트 POST + 25MB 상한 (multipart 아님) | 1 |
| Z4 | 소프트 삭제 + 복원 | 1 |
| Z5 | 빈 우선순위는 경고 (오류 아님) | 1 |
| Z6 | 기타 칸 = 사람 메모 + 마지막 줄 `id:… \| src:…` | 1 |
| Z7 | 라이브러리 저장 `state/tc_library/{suite}/` (gitignore) | 1 |
| Z8 | case_id 접두어는 가져오기 화면에서 시트별 입력 | 1 |
| Y1~Y7 | 생성 세션 도구 없음(`--restricted --tools ""`) · `--json-schema` 구조화 출력 · 폴링 · 구조 오류만 버림 · 인용 불일치 배지 · `/api/tc-library/*` 경로 · 중복 갱신 규칙 | 2 |
| X1~X7 | REST 수집(MCP 아님) · `flags.source_change` · 확인 완료는 버전만 교체 · 번들 옛 본문과 비교 · 표준 라이브러리 HTML 변환 · Figma 이미지는 검토 화면 전용 · 연결 설정 창 | 3 |
| V1~V5 | `data_key` = `{프로덕트}.{데이터셋}` · 충돌 건너뛰기만 exclude + overwrite 정책 · 드리프트 충돌 · 롤백 시 내보내기 기록 복원 · 표준 태그 | 4 |

## 4. 작업 진행 방법

1. [개발 인수인계](TC_AUTHORING_HANDOFF.md)의 절차를 따른다.
2. 위 표에서 현재 Phase 계획을 열고, 작업 ID 순서대로 진행한다 (앞 작업의 테스트가 통과해야 다음으로).
3. 테스트 → 구현 → 테스트 통과 → 커밋. 커밋 메시지에 작업 ID를 넣는다 (`feat(tc-studio): B3 …`).
4. 반복 실수를 찾으면 [lessons_learned.md](../../../agents/lessons_learned.md)에 기록한다 (CLAUDE.md 규칙).
5. Phase의 마지막 문서 작업(W4·W8·W11·W13)에서 이 표의 해당 Phase에 `✅ 완료 (날짜)`를 붙인다.

## 5. Import 기능 통합 후속 작업

초기 Phase 4는 md 내보내기 구현 완료 기록입니다. 별도 Import 화면의 제거는 사용자 승인 후 [통합 계획](plans/2026-09-30-import-integration.md)으로 추가 수행했습니다. 프로필 CRUD·source_tc_id/태그·다중 파일·시트별 매핑·행별 변경 미리보기·충돌 선택·가져오기 작업 복구·기존 md 이력 접근을 TC 화면에 연결했습니다. 기존 API·공용 md 엔진·기록 자료는 유지합니다.

다중 파일의 동일 시트 이름은 한 작업에 가져오지 못합니다. 실제 브라우저 검증과 전체 회귀 최종 수치는 [구현 보고](TC_AUTHORING_IMPLEMENTATION_REPORT.md)를 확인합니다.

2026-09-30 후속 사용자 요청으로 자동화 여부 필드와 관련 기능을 제거합니다. 초기 Phase 계획은 당시 구현·검증 기록이며 현재 md 대상 조건은 승인·검증·문구 확인·그룹 연결입니다.
