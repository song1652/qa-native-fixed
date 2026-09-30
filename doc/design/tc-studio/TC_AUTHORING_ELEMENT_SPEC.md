# TC 스튜디오 요소 동작 명세

> **설계 참고 문서**: 최초 설계와 제안이 포함되어 있으며, 현재 화면과 일부 차이가 있을 수 있습니다. 사용 방법은 [사용자 설명서](../../guides/tc-studio/TC_AUTHORING_USER_GUIDE.md), 실제 구현과 확인 범위는 [구현 보고](../../development/tc-studio/TC_AUTHORING_IMPLEMENTATION_REPORT.md)를 참고하세요.

| 항목 | 내용 |
|---|---|
| 기준 문서 | [TC_AUTHORING_PRD.md](TC_AUTHORING_PRD.md) Draft v0.3 |
| 목업 | [design-previews/tc-authoring-studio.html](../../../design-previews/tc-authoring-studio.html) (요소 ID = 목업의 `data-id` 속성) |
| 작성일 | 2026-09-29 |
| 시각 규칙 | Import Studio([`agents/dashboard/static/css/import-studio.css`](../../../agents/dashboard/static/css/import-studio.css))의 토큰, 버튼(`btn-primary`/`btn-ghost`/`btn-sm`/`btn-success`), 스테퍼(`step-circle`/`step-line`), 상태 배지 색(add=초록, update=파랑, conflict=노랑, error=빨강)을 그대로 쓴다. 대시보드가 다크 우선이므로 다크가 기본이고, 목업은 라이트 변형도 포함한다. |

## 0. 표기 규칙

- **동작** 칸은 `트리거 → 결과` 형식이다.
- **상태** 칸의 약어: 기본 / hover / disabled / loading / error. 적지 않은 상태는 공통 규칙(1.4)을 따른다.
- **API** 칸의 엔드포인트는 제안안이다. 상태를 바꾸는 POST·PATCH·PUT·DELETE에는 모두 `_check_csrf_origin`을 적용한다(PRD §7 쓰기 보호). 요약은 8장에 있다.
- 작성·검토 상태 값: `draft`(초안), `approved`(승인), `rejected`(반려), `needs_review`(재검토 필요). 실행 결과 `Pass`/`Fail`/`Not Test`/`N/A`와 별개다. 검증 오류는 별도 배지다(F5.8).
- UI 문구 신뢰도: `확인`(verified=true), `추정`(verified=false) (F5.7).

---

## 1. 공통

### 1.1 헤더와 화면 전환

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `suite-select` | 스위트 선택 드롭다운 | 헤더 제목 오른쪽 | 변경 → 라이브러리·트리·필터 초기화 후 선택한 스위트 로드. 편집 중인 변경이 있으면 "저장하지 않은 변경 n건" 확인 모달을 먼저 띄움 | 기본 / loading(드롭다운 옆 스피너) | 목록은 `state/tc_library/*.json` 파일 기준 | `GET /api/tc-library` | §5, F5.1 |
| `btn-import-xlsx` | 엑셀 가져오기 버튼 | 헤더 오른쪽 | 클릭 → `import-modal` 열림 | 기본 / hover / disabled(가져오기 작업 진행 중) | — | — | F2.1~F2.4 |
| `demo-state` | 목업 상태 전환 | 헤더 오른쪽(점선 상자) | **목업 전용.** 기본 / 빈 라이브러리 / 소스 버전 변경 / rev 충돌 / 생성 작업 실패 상태를 재현 | — | 실제 제품에는 넣지 않음 | — | — |
| `nav-tab-library` | 탭 1: TC 라이브러리 | 헤더 하단 스테퍼 | 클릭 → 라이브러리 화면. 배지에 스위트 케이스 수 | 선택 시 보라 원 + 글로우(Import Studio `step-circle.active`) | — | — | F5.1 |
| `nav-tab-generate` | 탭 2: 새로 생성 | 스테퍼 | 클릭 → 생성 화면. 진행 중 작업이 있으면 원 안에 스피너 | 동일 | — | — | F1, F4 |
| `nav-tab-review` | 탭 3: 초안 검토 | 스테퍼 | 클릭 → 검토 화면. 배지 = 미검토 초안 수(0이면 숨김) | 동일 | — | `GET /api/tc-library/{suite}?status=draft&count_only=1` | F5.5 |
| `nav-tab-export` | 탭 4: 내보내기 | 스테퍼 | 클릭 → 내보내기 화면 | 동일 | — | — | F6, F7 |

> 스테퍼 모양을 쓰지만 순서를 강제하지 않는다. 네 화면은 언제든 오갈 수 있다. 마지막으로 연 탭은 브라우저에 기억한다(개인 편의). URL 해시 `#library` `#generate` `#review` `#export`로 바로 열 수 있다.

### 1.2 토스트

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `toasts` (컨테이너) | 토스트 스택 | 화면 오른쪽 아래 | 성공(초록 테두리) 1.8~3.8초 뒤 사라짐. 오류·충돌 토스트는 사용자가 닫을 때까지 유지 | ok / warn / err | 최대 3개 쌓임, 초과 시 가장 오래된 것부터 제거. `aria-live="polite"` | — | — |
| `toast-conflict-compare` | 충돌 토스트: 차이 비교 | rev 충돌 토스트 | 클릭 → 해당 케이스 상세 패널을 열고 `이력` 탭에 "내 값 / 서버 값" 비교 표시 | — | 내 변경은 버리지 않고 패널에 남김 | `GET /api/tc-library/{suite}/cases/{case_id}` | F5.2 |
| `toast-conflict-reload` | 충돌 토스트: 최신 값 불러오기 | rev 충돌 토스트 | 클릭 → 서버 값으로 덮고 rev 갱신. 내 변경은 버림 | — | — | `GET /api/tc-library/{suite}/cases/{case_id}` | F5.2 |
| `bulk-undo` / `delete-undo` / `draft-undo` | 되돌리기 | 일괄 편집·삭제·검토 결정 토스트 | 클릭 → 직전 작업 역적용(되돌린 것도 이력에 남음) | 토스트가 사라지면 기회 종료. 이후엔 이력 패널에서 되돌림 | 되돌리는 시점에 rev가 또 바뀌었으면 충돌 토스트 | `POST /api/tc-library/{suite}/cases/{case_id}/revert` (일괄은 `POST /api/tc-library/{suite}/bulk` 역연산) | F5.11 |
| `toast-open-review` | 생성 완료 토스트: 검토하기 | 생성 완료 토스트 | 클릭 → 초안 검토 탭, 해당 job 초안으로 필터 | — | — | — | F4.3 |
| `toast-open-md-preview` | md 미리보기 토스트: 보기 | md 내보내기 토스트 | 클릭 → 같은 Studio의 내보내기 탭에서 `md-preview-panel`로 이동 | — | — | — | F7.2 |

### 1.3 공용 모달

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `confirm-modal` | 삭제 확인 모달 | 화면 중앙 | 삭제 요청 시 열림. "삭제한 케이스는 변경 이력에서 복원할 수 있습니다" 안내 | — | `confirm()`을 쓰지 않고 페이지 안 모달로 확인 | — | F5.3 |
| `confirm-ok` | 삭제 확정 | 모달 하단 | 클릭 → 삭제 요청, 모달 닫힘, 되돌리기 토스트 | loading | 각 케이스의 rev 동봉 | `DELETE /api/tc-library/{suite}/cases/{case_id}?rev=` (여러 건이면 `POST /api/tc-library/{suite}/bulk` op=delete) | F5.3 |
| `confirm-cancel` | 취소 | 모달 하단 | 클릭 또는 Esc → 닫힘 | — | — | — | — |
| `move-modal` | 계층 이동 모달 | 화면 중앙 | `bulk-move`/`detail-move` 클릭 시 열림 | — | — | `GET /api/tc-library/{suite}/tree` | F5.3 |
| `move-target` | 대상 가지 선택 | 이동 모달 | 시트 › 대분류 › 중분류 › 소분류 조합 선택 | — | 존재하는 가지만. 새 가지는 9장 피드백 #13 참고 | — | F5.3, F5.8 |
| `move-feature` | 기능명 | 이동 모달 | 비우면 기존 기능명 유지, 입력하면 기능명도 변경 | — | 앞뒤 공백 제거 | — | F5.3 |
| `move-confirm` | 이동 확정 | 이동 모달 | 클릭 → 이동, 토스트 "n건을 {경로}로 옮겼습니다" | loading / error(충돌 건 수 표시) | rev 동봉, 부분 성공 가능 | `POST /api/tc-library/{suite}/move` `{items:[{case_id,rev}], path, feature?}` | F5.3 |
| `move-close` / `move-cancel` | 닫기 | 이동 모달 | 클릭·Esc → 닫힘 | — | — | — | — |

### 1.4 공통 상태 규칙

- **hover**: 버튼은 한 단계 진한 배경, 셀·행은 `--card` 배경.
- **disabled**: 불투명도 45%, `cursor: not-allowed`, `title`에 비활성 사유를 적는다(예: "중복 처리 방법을 먼저 고르세요").
- **loading**: 버튼 안 왼쪽에 스피너, 같은 요청 중복 전송 금지.
- **error**: 입력칸은 빨간 테두리 + 아래 `help err` 문구. 요청 실패는 오류 토스트. 문구는 "무엇이 잘못됐는지 + 어떻게 고치는지"로 쓴다.
- **포커스**: 모든 인터랙티브 요소에 2px 보라 외곽선(`:focus-visible`).

---

## 2. TC 라이브러리 (F5.1~F5.4, F5.7~F5.9, F5.11)

3단 레이아웃: 왼쪽 계층 트리(250px), 가운데 그리드(가변), 오른쪽 상세 패널(380px). 1180px 미만에서는 상세 패널이 오른쪽에서 겹쳐 열리는 시트가 되고, 860px 미만에서는 트리가 그리드 위로 쌓인다. 그리드는 자체 컨테이너 안에서 가로 스크롤한다.

### 2.1 계층 트리

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `lib-tree` | 계층 트리 | 왼쪽 패널 | 시트(S) › 대분류(대) › 중분류(중) › 소분류(소) › 기능(기) 5단. 각 노드에 케이스 수와 상태 점(보라=초안, 노랑=재검토, 빨강=검증 오류). 점에 마우스를 올리면 "초안 3" 식으로 개수 | loading(스켈레톤 8줄) / error("트리를 불러오지 못했습니다. 다시 시도") | 1,000건 이상에서도 첫 표시 1초 이내(트리는 서버 집계값 사용) | `GET /api/tc-library/{suite}/tree` → `[{name, level, count, counts:{draft,needs_review,invalid}, children}]` | F2.2, F5.1 |
| `tree-node` | 트리 노드 | 트리 각 행 | 클릭·Enter·Space → (자식 있으면) 펼침/접힘 + 그 가지로 그리드 필터. 선택 노드는 보라 배경. 그리드 행(`grid-row-drag`)을 드롭하면 그 가지로 이동 | 기본 / hover / 선택 / 드롭 대상(보라 점선) | 드롭 대상이 시트 노드면 거부(대분류 이상 지정 필요) | 선택: `GET /api/tc-library/{suite}?path=…` / 드롭: `POST /api/tc-library/{suite}/move` | F5.1, F5.3 |
| `tree-search` | 가지 이름 검색 | 트리 위 | 입력 → 이름이 맞는 가지와 그 조상만 남기고 모두 펼침 | 결과 없음 → "맞는 가지가 없습니다" | 클라이언트 필터(트리는 이미 로드됨) | — | F5.4 |
| `tree-collapse-all` | 모두 접기 | 트리 위 오른쪽 | 클릭 → 시트 단계까지 접음 | — | — | — | — |

### 2.2 필터·검색 바

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `lib-search` | 전문 검색 | 필터 바 왼쪽 | 입력(300ms 디바운스) → 기능·사전 조건·Step·Expected·UI 문구에서 검색. 일치 부분을 그리드에서 강조 | 결과 0건 → `grid-empty-filter` | 2자 이상부터 서버 검색. `/` 키로 포커스 | `GET /api/tc-library/{suite}?q=` | F5.4 |
| `lib-filter-result` | 실행 결과 필터 | 필터 바 | 선택 → 해당 결과만 | — | 값: pass/fail/not_test/na | `?execution_result=` | F5.4 |
| `lib-filter-status` | 검토 상태 필터 | 필터 바 | 선택 → 해당 작성·검토 상태만 | — | 값: draft/approved/rejected/needs_review | `?status=` | F5.4 |
| `lib-filter-priority` | 우선순위 필터 | 필터 바 | 선택 → P0~P3/미지정 | — | "미지정"은 빈 값(가져온 케이스 대부분) | `?priority=` | F5.4 |
| `lib-filter-auto` | AUTO 필터 | 필터 바 | 선택 → Y-web/Y-app/N/미지정 | — | — | `?auto=` | F5.4 |
| `lib-filter-source` | 출처 필터 | 필터 바 | 선택 → 엑셀 가져오기 / Confluence / Figma / 파일·붙여넣기 | — | `source_refs` 접두사(`xlsx:`, `conf:`, `figma:`, `file:`)로 판정 | `?source=` | F5.4 |
| `lib-filter-needs-review` | 재검토 필요 토글 칩 | 필터 바 | 클릭 → 켜짐/꺼짐. 칩 안 숫자 = 재검토 필요 건수 | 켜짐=보라 테두리(`aria-pressed=true`) | — | `?needs_review=1` | F5.4, F5.9 |
| `lib-filter-invalid` | 검증 오류 토글 칩 | 필터 바 | 클릭 → 검증 오류가 있는 케이스만 | 동일 | — | `?invalid=1` | F5.4, F5.8 |
| `lib-filter-reset` | 초기화 | 필터 바 끝 | 클릭 → 검색어·필터·트리 선택 모두 해제 | 적용된 필터가 없으면 disabled | — | — | F5.4 |

필터 조합은 AND다. 현재 필터는 내보내기 화면의 "현재 필터 결과" 범위(`xlsx-scope`)에 그대로 넘어간다.

### 2.3 케이스 그리드

컬럼은 선택 | 끌기 | A No. | 실행 결과 | B 대분류 | C 중분류 | D 소분류 | E 기능 | F 사전 조건 | G Test Step | H Expected Result | I 우선순위 | M 기타(id · src) 순서다. AUTO는 그리드 셀에서 빼고 상세 패널·일괄 편집·필터에서 관리한다. 실행 결과는 TC당 하나로 표시한다(Excel의 And/iOS K/L 매핑은 PRD O7). 작성·검토 상태는 상세 패널과 필요할 때 기타 칸의 배지로 보여준다. 계층 값이 위 행과 같으면 흐리게 표시한다.

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `lib-grid` | 그리드 | 가운데 | 행 클릭(편집 중 셀·입력·칩 제외) → 오른쪽 상세 패널에 그 케이스. 활성 행은 보라 테두리 | loading(행 스켈레톤) / 빈 결과 → `grid-empty-filter` | 가상 스크롤. 한 번에 200행 요청, 스크롤로 이어 받음. 헤더 행 sticky | `GET /api/tc-library/{suite}?path=&…&offset=&limit=200` | F5.1, §7 성능 |
| `grid-check-all` | 전체 선택 | 헤더 첫 칸 | 체크 → 현재 필터 결과 전체 선택(가상 스크롤 밖 포함, "필터 결과 186건 모두 선택됨" 안내) | 일부 선택 시 indeterminate | — | — | F5.3 |
| `grid-row-check` | 행 선택 | 각 행 첫 칸 | 체크 → 선택 집합에 추가, `bulk-bar` 표시. Shift+클릭 범위 선택 | — | — | — | F5.3 |
| `grid-row-drag` | 행 끌기 핸들 | 각 행 둘째 칸 | 끌어서 트리 노드에 놓기 → 계층 이동. 그리드 안에서 위아래로 놓기 → 같은 가지 안 순서 변경(엑셀 행 순서) | 끄는 중 반투명 | 다른 시트로는 이동 불가(경고 토스트) | `POST /api/tc-library/{suite}/move` / 순서: `PATCH /api/tc-library/{suite}/cases/{case_id}` `{order, rev}` | F5.3, F6.2 |
| `grid-cell-feature` | 기능 셀 (E) | 그리드 | 더블클릭 또는 Enter → 제자리 편집. ⌘/Ctrl+Enter 또는 포커스 이탈 → 저장. Esc → 취소 | 편집 중(보라 외곽선) / 저장 중(파란 점선) / error(빨강) | 빈 값 금지(필수 컬럼) | `PATCH /api/tc-library/{suite}/cases/{case_id}` `{rev, feature}` → 200 `{case}` / 409 `{server_case}` | F5.2, F5.8 |
| `grid-cell-precondition` | 사전 조건 셀 (F) | 그리드 | 위와 같음. 편집 중 Enter는 줄바꿈 | 동일 | "- " 불릿 줄 권장(경고 아님) | `PATCH …` `{rev, precondition}` | F5.2 |
| `grid-cell-steps` | Test Step 셀 (G) | 그리드 | 위와 같음. 줄마다 "1. …" 형식으로 편집. 저장 시 줄 단위로 `steps[]` 배열화 | error: 번호 없는 줄이 있으면 저장 거부, 셀 빨강 + 토스트 "Test Step은 줄마다 '1. …' 형식이어야 합니다" | 번호 연속성 검사, 빈 줄 제거 | `PATCH …` `{rev, steps:[…]}` | F5.2, F5.8 |
| `grid-cell-expected` | Expected Result 셀 (H) | 그리드 | 위와 같음. 첫 줄 = 결과 문장, "- "로 시작하는 줄 = UI 문구 불릿. 추정 문구는 노랑 글자 + "(추정)" | 모호한 표현이 있으면 저장은 하되 경고 토스트 + 셀 아래 `검증 오류` 배지 | 금지 표현 목록은 작성 프로필 값 | `PATCH …` `{rev, expected, expected_bullets}` | F5.2, F5.7, F5.8 |
| `grid-cell-priority` | 우선순위 칩 (I) | 그리드 | 칩 드롭다운 선택 → 즉시 저장 | P0 빨강 / P1 노랑 / P2 파랑 / P3 회색 / 미지정 이탤릭 회색 | 허용값: `P0`~`P3` (템플릿 드롭다운은 `P0,P1,P2`뿐이라 엑셀 내보내기 때 목록을 넓힘) | `PATCH …` `{rev, priority}` | F5.2, F5.8 |
| `grid-result` | 실행 결과 셀 | 그리드 No. 뒤 | Pass/Fail/Not Test/N/A 선택 → 즉시 저장 | Pass 초록 / Fail 빨강 / Not Test 회색 / N/A 노랑 | 서버 값: pass/fail/not_test/na, 신규 초안 기본 not_test | `PATCH …` `{rev, execution_result}` | F5.2 |
| `grid-status-chip` | 검토 상태 배지 | 그리드 기타 칸·상세 패널 | 초안·반려·재검토 필요를 표시(변경은 상세 패널·일괄 바) | draft 보라 / rejected 빨강 / needs_review 노랑 | 승인된 행은 그리드에서 생략 가능 | — | F5.5, F5.9 |
| `grid-source-ref` | 출처 칩 (M) | 그리드 기타 칸 | 클릭 → 상세 패널 `원문` 탭. 소스 버전이 바뀌면 "conf:…@v14 → v15" 표시 | — | 기타 칸 첫 줄은 항상 `id:{case_id}` | — | F5.9, F6.5 |
| `btn-add-case` | 케이스 추가 | 그리드 위 오른쪽 | 클릭 → 현재 활성 케이스(또는 선택한 가지) 아래에 빈 초안 행 추가, 상세 패널에서 기능명 입력칸 선택 | loading | 새 `case_id`는 서버가 발급(시트 접두사 + 일련번호) | `POST /api/tc-library/{suite}/cases` `{path, after_case_id}` | F5.3 |
| `grid-empty-filter` | 필터 결과 없음 | 그리드 본문 | "조건에 맞는 케이스가 없습니다" + 필터 초기화 버튼 | — | — | — | F5.4 |

### 2.4 일괄 편집 바

여러 행을 선택하면 그리드 아래에 떠 있는 바가 나타난다.

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `bulk-bar` | 일괄 편집 바 | 그리드 하단(sticky) | 1건 이상 선택 시 표시. "n건 선택" | — | — | — | F5.3 |
| `bulk-priority` | 우선순위 일괄 변경 | 바 | 값 선택 → 선택 전체에 적용, 되돌리기 토스트 | loading | 각 항목 rev 동봉. 일부 충돌 시 "n건 중 1건(BEN_0009)은 다른 곳에서 바뀌어 건너뛰었습니다" 경고 | `POST /api/tc-library/{suite}/bulk` `{items:[{case_id,rev}], op:"set", field:"priority", value}` → `{updated:[…], conflicts:[…]}` | F5.3 |
| `bulk-auto` | AUTO 일괄 변경 | 바 | 동일 | 동일 | 동일 | 동일 field:"auto" | F5.3 |
| `bulk-result` | 실행 결과 일괄 변경 | 바 | Pass/Fail/Not Test/N/A 선택 → 선택 전체에 적용 | loading | 각 항목 rev 동봉, 충돌은 건별 안내 | 동일 field:"execution_result" | F5.3 |
| `bulk-status` | 검토 상태 일괄 변경 | 바 | 승인 / 초안으로 / 반려 | 동일 | 검증 오류가 있는 케이스는 승인에서 제외하고 건수 안내 | 동일 field:"status" | F5.3, F5.8 |
| `bulk-move` | 계층 이동 | 바 | 클릭 → `move-modal` | — | — | — | F5.3 |
| `bulk-duplicate` | 복제 | 바 | 클릭 → 새 case_id로 복제, 초안 상태로 원본 바로 아래 | loading | source_refs는 복사, 이력은 새로 시작 | `POST /api/tc-library/{suite}/bulk` op:"duplicate" | F5.3 |
| `bulk-delete` | 삭제 | 바 | 클릭 → `confirm-modal` | — | — | op:"delete" | F5.3 |
| `bulk-clear` | 선택 해제 | 바 오른쪽 | 클릭 또는 Esc → 선택 해제, 바 숨김 | — | — | — | — |

### 2.5 상세 패널

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `detail-panel` | 상세 패널 | 오른쪽 | 활성 케이스의 전체 편집기. 헤더에 case_id, 상태 배지, rev, 저장 안 한 변경 점(노랑) | loading / error("케이스를 찾을 수 없습니다. 삭제됐을 수 있습니다") | 저장 안 한 변경이 있는데 다른 행을 누르면 "저장 / 버리기 / 취소" 확인 | `GET /api/tc-library/{suite}/cases/{case_id}` | F5.1 |
| `detail-close` | 닫기 | 패널 헤더 | 클릭 → 패널 닫고 그리드 넓힘 | — | 변경 있으면 확인 | — | — |
| `detail-feature` | 기능명 입력 | 패널 헤더 | 입력 → 변경 표시 | error: 빈 값 | 필수 | 저장 시 일괄 PATCH | F5.2 |
| `detail-move` | 경로 이동 | 패널 헤더 경로 옆 | 클릭 → `move-modal` | — | — | — | F5.3 |
| `detail-tab-edit` / `detail-tab-source` / `detail-tab-history` | 편집 · 원문 · 이력 탭 | 패널 탭 줄 | 클릭 → 해당 탭 | 선택 탭 밑줄 | — | 원문: `GET /api/tc-library/sources/{bundle}/excerpt?ref=` / 이력: `GET /api/tc-library/{suite}/cases/{case_id}/history` | F5.5, F5.11 |
| `detail-priority` / `detail-auto` / `detail-result` / `detail-status` | 우선순위 · AUTO · 실행 결과 · 검토 상태 | 편집 탭 상단 | 변경 → 변경 표시 | — | 검토 상태를 approved로 바꿀 때 검증 오류가 있으면 저장 거부 | 저장 시 PATCH | F5.2, F5.8 |
| `detail-precondition` | 사전 조건 | 편집 탭 | 입력 | — | — | 저장 시 PATCH | F5.2 |
| `detail-steps` | Step 목록 | 편집 탭 | 줄마다 번호 자동 표시(입력칸에는 번호 없이) | — | 빈 Step이 있으면 저장 거부 | 저장 시 PATCH `steps[]` | F5.2 |
| `detail-step-drag` | Step 끌기 핸들 | 각 Step 왼쪽 | 끌어서 놓기 → 순서 변경, 번호 다시 매김. 키보드: 입력칸에서 Alt+↑/↓ | 끄는 중 반투명, 놓을 곳 보라 테두리 | — | — | F5.2 |
| `detail-step-input` | Step 입력칸 | 각 Step | 입력. Enter → 아래에 새 Step 추가 후 포커스 | — | — | — | F5.2 |
| `detail-step-remove` | Step 삭제 | 각 Step 오른쪽 | 클릭 → 줄 삭제, 번호 다시 매김 | — | Step 최소 1개 | — | F5.2 |
| `detail-step-add` | Step 추가 | Step 목록 아래 | 클릭 → 끝에 빈 줄, 포커스 | — | — | — | F5.2 |
| `detail-expected` | Expected 문장 | 편집 탭 | 입력. 모호한 표현이면 아래 빨간 도움말 | error 도움말 | 금지 표현은 프로필 값 | 저장 시 PATCH | F5.8 |
| `detail-bullets` | UI 문구 목록 | 편집 탭 | 문구마다 `확인`/`추정` 배지 + 입력칸 + 삭제 | — | — | — | F5.7 |
| `detail-bullet-verify` | 확인/추정 배지 | 각 문구 왼쪽 | 클릭 → verified 토글. 추정으로 바꾸면 툴팁 "md 내보내기에서 제외됩니다" | 확인=초록 / 추정=노랑 | 추정 문구가 하나라도 있으면 그 케이스는 md 대상에서 빠짐 | 저장 시 PATCH `expected_bullets[{text, verified}]` | F5.7, F7.1 |
| `detail-bullet-input` / `detail-bullet-remove` / `detail-bullet-add` | 문구 입력 · 삭제 · 추가 | UI 문구 영역 | 입력 / 삭제 / 새 문구(기본 추정) 추가 | — | 새로 쓴 문구의 기본값은 `추정` | — | F5.7 |
| `detail-source-ref` | 출처 칩 | 편집 탭 하단 | 클릭 → `원문` 탭. 소스가 바뀌었으면 옆에 "v14 → v15 바뀜" 노랑 태그 | — | — | — | F5.9 |
| `detail-validation` | 검증 목록 | 편집 탭 맨 아래 | 필수 컬럼 / 허용 우선순위 / Step 번호 / 모호한 표현 / 계층 경로 5개 항목을 ✓·!·✕로 표시 | ✓ 초록 / ! 노랑(미지정 경고) / ✕ 빨강 | 저장 때마다 서버가 다시 계산 | PATCH 응답의 `validation[]` | F5.8 |
| `detail-mark-reviewed` | 변경 확인 완료 | 원문 탭(소스 버전 변경 시) | 클릭 → 출처를 새 버전(`@v15`)으로 올리고 재검토 표시 해제. 원문 탭에 v14↔v15 바뀐 문장 diff 표시 | loading | 케이스 내용을 고치지 않고 확인만 해도 해제 가능 | `POST /api/tc-library/{suite}/cases/{case_id}/ack-source` `{ref, to_version, rev}` | F5.9 |
| `detail-add-source-ref` | 출처 문서 연결 | 원문 탭(엑셀에서 가져온 케이스) | 클릭 → 수집된 소스 목록에서 골라 source_ref 추가 | — | 9장 #7 참고 | `PATCH …` `{rev, source_refs}` | 목표 5 |
| `detail-history` | 변경 이력 | 이력 탭 | 시간, 사람, 필드, 이전→이후 diff(삭제 빨강 취소선, 추가 초록) | 빈 이력 → "아직 바뀐 적이 없습니다" | `history.jsonl`에서 읽음 | `GET /api/tc-library/{suite}/cases/{case_id}/history` | F5.11 |
| `detail-history-revert` | 이 값으로 되돌리기 | 각 이력 항목 오른쪽 | 클릭 → 해당 필드를 이전 값으로. 되돌린 것도 새 이력 행 | loading / 충돌 시 충돌 토스트 | 생성·가져오기 행에는 버튼 없음 | `POST /api/tc-library/{suite}/cases/{case_id}/revert` `{history_id, rev}` | F5.11 |
| `detail-save` | 저장 | 패널 하단 | 클릭 또는 ⌘/Ctrl+S → 바뀐 필드만 PATCH. 성공 토스트 "BEN_0009 저장됨 · rev 6" | 변경 없으면 disabled / loading / 409 → 충돌 토스트(내 변경 유지) | rev 필수 | `PATCH /api/tc-library/{suite}/cases/{case_id}` `{rev, …changed}` | F5.2 |
| `detail-revert-edits` | 변경 취소 | 패널 하단 | 클릭 → 저장 안 한 변경 버리고 서버 값으로 | 변경 없으면 disabled | — | — | — |
| `detail-duplicate` | 복제 | 패널 하단 오른쪽 | 클릭 → 초안 상태 사본 생성, 사본으로 패널 전환 | loading | — | `POST /api/tc-library/{suite}/cases/{case_id}/duplicate` | F5.3 |
| `detail-delete` | 삭제 | 패널 하단 오른쪽 | 클릭 → `confirm-modal` | — | — | `DELETE /api/tc-library/{suite}/cases/{case_id}?rev=` | F5.3 |

### 2.6 라이브러리의 특수 상태

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `lib-empty` | 빈 라이브러리 | 가운데 전체 | 스위트에 케이스가 0건이면 트리·필터·그리드 대신 표시. 엑셀 아이콘, 설명, 두 버튼 | — | — | — | F2.4 |
| `empty-import-xlsx` | 엑셀 가져오기 (주 버튼) | 빈 상태 | 클릭 → `import-modal` | — | — | — | F2 |
| `empty-generate` | 문서로 새로 생성 | 빈 상태 | 클릭 → 새로 생성 탭 | — | 빈 라이브러리면 문체 예시(F2.5)가 없다는 안내를 생성 화면에 표시 | — | F4 |
| `banner-source-changed` | 소스 변경 배너 | 필터 바 위 | 소스 버전 변화 감지 시 노랑 배너: "{문서} v14 → v15 · 관련 케이스 6건이 재검토 필요" | — | 배너는 재검토 건이 0이 되면 사라짐 | `GET /api/tc-library/{suite}/source-changes` (표시된 변경 조회; 원격 버전 확인은 사용자가 요청한 POST …/scan에서만) | F5.9 |
| `banner-review-now` | 6건만 보기 | 배너 | 클릭 → `lib-filter-needs-review` 켬 | — | — | — | F5.9 |
| `banner-diff` | 바뀐 부분 보기 | 배너 | 클릭 → 첫 재검토 케이스의 원문 탭(diff 포함) | — | — | `GET /api/tc-library/source-diff?ref=conf:48213377&from=14&to=15` | F5.9 |

**rev 충돌** (목업 상태 `rev 충돌`): 셀·패널·일괄 저장이 409를 받으면 값을 되돌리지 않고 오류 토스트를 띄운다. 토스트는 자동으로 닫히지 않는다. 문구: "BEN_0009를 저장하지 못했습니다. 다른 곳에서 먼저 바뀌었습니다 (내 rev 5, 서버 rev 6). 변경 내용은 그대로 남아 있습니다." 버튼은 `toast-conflict-compare`, `toast-conflict-reload` 두 개다. v1은 단일 사용자이므로 "덮어쓰기"는 넣지 않는다(비교 후 수동 반영).

### 2.7 엑셀 가져오기 모달

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `import-modal` | 가져오기 모달 | 화면 중앙 | 파일을 고르면 서버가 분석한 결과(헤더 행, 시트별 행 수·가지 수, 경고)를 표시. 기준 양식은 자동 매핑, 다른 양식은 컬럼 매핑으로 전환 | loading(분석 중) / error(헤더 탐지 실패 시 수동 매핑 안내) | .xlsx만, 25MB 이하, 매직바이트 검사 | `POST /api/tc-library/import/preview` (multipart) → `{preview_id, header_row, subheader_row, sheets:[{name, rows, branches}], warnings[]}` | F2.1, F2.2, F2.6 |
| `import-pick-file` | 파일 바꾸기 | 모달 파일 카드 | 클릭 → 파일 선택, 다시 분석 | — | 원본 파일은 읽기만 함 | 위와 같음 | F2.1 |
| `import-mapping-mode` | 기준 양식 자동 매핑 / 다른 양식 직접 매핑 | 모달 파일 카드 아래 | 변경 → 헤더 행·컬럼 매핑과 프로필 선택 표시 또는 숨김 | — | 필수 필드 매핑을 마치기 전에는 가져오기 disabled | — | F2.1 |
| `import-mapping-profile` | 저장한 매핑 프로필 | 직접 매핑 영역 | 선택 → 헤더·컬럼 매핑값 채움. 새 이름으로 저장 가능 | — | 기존 Import Studio 프로필을 읽어 이전 | `GET /api/tc-library/import/profiles`, `PUT /api/tc-library/import/profiles/{name}` | F2.1, D6 |
| `import-column-mapping` | 헤더 행·필수 컬럼·그룹 매핑 | 직접 매핑 영역 | 변경 → 샘플 행 미리보기와 오류 건수 갱신 | — | 제목·Step·Expected 및 `case_id` 생성/매핑 규칙 필수 | `POST /api/tc-library/import/preview` | F2.1 |
| `import-sheets` | 가져올 시트 체크 목록 | 모달 | 시트별 체크. History처럼 TC 헤더가 없는 시트는 disabled | — | 최소 1개 | — | F2.2 |
| (경고 목록) | 분석 결과 체크리스트 | 모달 | 병합 해제 결과, template_profile 저장, `#REF!` 요약 수식, 우선순위·AUTO 공란, K/L 결과 컬럼 미수입 안내 | ✓ / ! | — | — | F2.3, F2.6, F6.3 |
| `import-confirm` | n건 가져오기 | 모달 하단 | 클릭 → 가져오기 실행. 완료 토스트 "926건을 가져왔습니다. 시트 6개 · 가지 31개" | loading | 이미 같은 case_id(`기타`의 `id:`)가 있으면 새로 추가하지 않고 **갱신**. 갱신 건수 따로 표시 | `POST /api/tc-library/import` `{preview_id, sheets[]}` → `{created, updated, skipped}` | F2.4, F6.7 |
| `import-cancel` / `import-close` | 취소 · 닫기 | 모달 | 닫힘, preview 폐기 | — | — | — | — |

---

## 3. 새로 생성 (F1, F2.5, F3, F4)

왼쪽: 소스 입력과 수집 결과. 오른쪽: 대상 위치, 작성 프로필, 생성 버튼과 작업 진행.

### 3.1 소스 입력

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `src-tab-file` / `src-tab-paste` / `src-tab-url` / `src-tab-confluence` / `src-tab-figma` | 소스 종류 탭 | 소스 패널 상단 | 클릭 → 해당 입력 영역. PRD 파일과 PRD URL은 동일한 문서 소스로 처리 | 선택 탭 보라 | 여러 종류를 섞어 넣을 수 있음 | — | F1 |
| `src-file-drop` | 파일 드롭존 | 파일 탭 | 파일을 끌어다 놓기 또는 클릭 → 업로드 후 소스 카드 추가 | hover·dragover 보라 / loading(카드에 "수집 중") / error 토스트 | .pdf .docx .md .txt, 25MB 이하, 매직바이트 검사, PDF 200쪽 이하. 초과 시 413 → "25MB를 넘습니다" | `POST /api/tc-library/sources/{bundle}/{kind}` (multipart, kind=file) → manifest 항목 | F1.1, §7 업로드 |
| `src-file-input` | 숨은 파일 입력 | 파일 탭 | 드롭존 클릭 시 열림 | — | accept 속성으로 1차 거름, 서버가 최종 검사 | 위와 같음 | F1.1 |
| `src-paste` | 붙여넣기 입력칸 | 붙여넣기 탭 | 입력 → 아래 크기 표시 "12.4 KB / 1 MB" | 1MB 초과 시 빨강, 추가 버튼 disabled | 1MB 이하 | — | F1.2 |
| `src-paste-add` | 소스로 추가 | 붙여넣기 탭 | 클릭 → 소스 카드 추가(`file:sha256…#paste`) | 빈 입력이면 오류 토스트 | — | `POST /api/tc-library/sources/{bundle}/{kind}` `{kind:"paste", text}` | F1.2 |
| `src-prd-url` / `src-prd-url-fetch` | PRD URL 입력·수집 | PRD URL 탭 | HTTPS 문서 URL 입력 → HTML/PDF/DOCX/Markdown/텍스트 추출 후 소스 카드 추가 | loading / error(접근 제한·지원하지 않는 형식·크기 초과) | 로그인·스크립트 렌더링이 필요한 일반 URL은 파일 업로드 또는 전용 연결 안내 | `POST /api/tc-library/sources/{bundle}/{kind}` `{kind:"url", url}` | F1.3 |
| `src-confluence-url` | Confluence URL | Confluence 탭 | 입력 | error: ID를 못 뽑으면 빨강 + "페이지 ID를 찾을 수 없습니다. /pages/{id} 또는 pageId= 가 들어간 주소를 넣어 주세요." | 클라이언트는 형식만 검사. 서버는 URL에서 ID만 뽑고 설정된 base로 요청 조립(SSRF) | — | F1.3, §7 SSRF |
| `src-confluence-children` | 하위 페이지 포함 | Confluence 탭 | 체크 → 깊이 1, 최대 20개 수집 | — | 20개를 넘으면 카드에 "잘림" 경고 | 요청 파라미터 `include_children` | F1.3 |
| `src-confluence-fetch` | 수집 | Confluence 탭 | 클릭 → 카드 추가(수집 중) → 완료 시 글자 수·이미지 수·표 수·버전 표시 | loading / error 카드(빨간 태그: "권한 없음 403", "연결 설정이 없습니다") | 타임아웃 15초, 20MB | `POST /api/tc-library/sources/{bundle}/{kind}` `{kind:"confluence", url, include_children}` | F1.3, F1.5, F1.6 |
| `src-figma-url` | Figma URL | Figma 탭 | 입력 | error: "/file/ 또는 /design/ 주소를 넣어 주세요" | fileKey·node-id 추출 | — | F1.4 |
| `src-figma-fetch` | 수집 | Figma 탭 | 클릭 → 카드(프레임 수, TEXT 수, 전이 수, lastModified) | loading / error | PNG 최대 10장 | `POST /api/tc-library/sources/{bundle}/{kind}` `{kind:"figma", url}` | F1.4, F1.6 |
| `cred-status-confluence` / `cred-status-figma` | 연결 상태 태그 | 소스 패널 | 설정됨: 초록 "Confluence 연결됨 · qa****@example.com". 미설정: 회색 "연결 안 됨" + 해당 탭 수집 버튼 disabled | — | 토큰은 절대 표시·반환하지 않음(`{configured, base_url, email_masked}`만) | `GET /api/tc-library/credentials` | §7 자격증명 |
| `cred-settings` | 연결 설정 | 소스 패널 | 클릭 → 설정 시트(base URL, 이메일, 토큰 입력. 저장 후 토큰은 다시 보여주지 않음) | — | 환경변수가 있으면 "환경변수 사용 중" 표시하고 입력 disabled | `PUT /api/tc-library/credentials/{confluence|figma}` | §7, Phase 3 |
| `src-list` | 수집한 소스 목록 | 소스 패널 하단 | 소스마다 카드 | 비었으면 "아직 수집한 소스가 없습니다" | — | — | F1.6 |
| `src-chip` | 소스 카드 | 목록 | 아이콘(C/F/PDF/T), 제목, `source_ref` 칩(버전 포함), 글자 수·이미지 수·표·프레임 태그, 잘림/OCR 미지원 경고(노랑), 실패(빨강) | 수집 중(파랑 태그) / 경고 / 실패 | — | — | F1.5, F1.6 |
| `src-chip-remove` | 소스 제거 | 카드 오른쪽 | 클릭 → 번들에서 제외 | — | 생성 중에는 disabled | `DELETE /api/tc-library/sources/{bundle}/{source_id}` | F1.5 |

### 3.2 대상 위치와 프로필

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `gen-target-sheet` | 대상 시트 | "어디에 넣을까요" 패널 | 선택 → 대분류 목록 갱신. 괄호 안 케이스 수 | — | 필수 | `GET /api/tc-library/{suite}/tree` | F2.2 |
| `gen-target-path` | 계층 선택기 | 같은 패널 | 대분류 › 중분류 › 소분류 연쇄 드롭다운 | — | 대분류 필수, 나머지 선택 | — | F2.2 |
| `gen-path-l1` / `gen-path-l2` / `gen-path-l3` | 대·중·소분류 | 계층 선택기 | 선택. "+ 새 중분류…" 선택 시 이름 입력칸 표시 | — | 새 이름은 같은 부모 안 중복 불가 | — | F2.2 (9장 #13) |
| `gen-style-examples` | 문체 예시 안내 | 계층 선택기 아래 | 선택한 가지의 기존 케이스 중 프롬프트에 넣을 예시 목록. 5건 미만이면 "권장 5~10건" 안내 | — | 최대 10건 | `GET /api/tc-library/{suite}?path=…&limit=10&status=approved` | F2.5 |
| `gen-profile` | 작성 프로필 선택 | 작성 프로필 패널 | 선택 → 아래 규칙 요약 갱신. "+ 새 프로필로 저장…" | — | — | `GET /api/tc-library/profiles` | F3 |
| `gen-profile-edit` | 프로필 편집 | 패널 헤더 | 클릭 → 편집 시트(커버리지, 조건 분기, 우선순위 기준, AUTO 판정, 문체, 금지 표현) | — | 이름 필수, 금지 표현은 줄 단위 | `PUT /api/tc-library/profiles/{name}` | F3 |

### 3.3 생성 실행과 진행

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `gen-submit` | 초안 생성 | 생성 패널 | 클릭 → 작업 생성, 진행 표시. 옆 도움말 "소스 2개 · 약 18,400자 · 예상 2분" | 수집 성공 소스 0개면 disabled / loading(작업 중) / 다른 작업이 돌고 있으면 disabled + "다른 생성 작업이 진행 중입니다" | 한 번에 1건(F4.1). 실패 후에는 "다시 생성"으로 바뀜 | `POST /api/tc-library/{suite}/jobs` `{suite, sheet, path, profile, source_ids[], example_case_ids[]}` → `{job_id}` (진행 중이면 409) | F4.1, F4.2 |
| `job-panel` | 작업 패널 | 생성 버튼 아래 | 작업 ID, 상태 배지, 5단계 진행 막대, 현재 단계 설명 | — | — | `GET /api/tc-library/jobs/{id}` + 1.5초 폴링 (Phase 2 결정 Y3) | F4.4 |
| `job-progress` | 단계 막대 | 작업 패널 | queued(대기) → fetching(수집) → drafting(초안 작성) → validating(검증) → done(완료). 끝난 단계 초록, 현재 보라, 실패 빨강 | — | 섹션 단위 생성이면 "섹션 3개 중 2번째 작성 중 · 초안 11건" | 1.5초 폴링 (Phase 2 결정 Y3) | F4.4, F4.5 |
| `job-cancel` | 취소 | 작업 패널 | 클릭 → 프로세스 종료, 패널 숨김, 토스트 | 완료·실패 후 숨김 | 이미 만든 초안 처리 정책은 9장 #11 | `POST /api/tc-library/jobs/{id}/cancel` | F4.1 |
| `job-log-tail` | 로그 끝부분 | 실패 박스 | 마지막 로그 줄(기본 40줄) 표시. 경고 노랑, 오류 빨강 | — | 소스 본문·토큰은 로그에 쓰지 않음 | `GET /api/tc-library/jobs/{id}` | F4.6 |
| (실패 박스) | 실패 요약 | 작업 패널 | 무엇이 실패했는지 한 줄(예: "초안 작성 단계에서 시간이 초과됐습니다 (180초)"), 살린 초안 수, invalid 수, 남은 섹션 | error | `claude` CLI 없음 / 타임아웃 / 부분 결과 세 경우를 구분해 문구 작성 | 응답 `{status:"failed", reason, partial, kept, invalid, failed_sections[]}` | F4.6 |
| `job-retry` | 실패한 섹션만 다시 생성 | 실패 박스 | 클릭 → 실패 섹션만 새 작업으로 | loading | — | `POST /api/tc-library/{suite}/jobs` `{retry_of: job_id, sections:[…]}` | F4.5, F4.6 |
| `job-open-review-partial` | 살린 초안 n건 검토 | 실패 박스 | 클릭 → 초안 검토 탭(이 작업 초안만) | — | — | — | F4.6 |
| `job-log-full` | 전체 로그 | 실패 박스 | 클릭 → 전체 로그 뷰어 | — | — | `GET /api/tc-library/jobs/{id}` | F4.6 |
| `job-open-review` | 초안 검토로 이동 | 완료 행 | 클릭 → 초안 검토 탭 | 초록 버튼 | — | — | F4.3 |

---

## 4. 초안 검토 (F5.5~F5.7, F5.10)

왼쪽: 초안 카드 목록. 오른쪽: 원문(Confluence 발췌 하이라이트 / Figma 프레임)과 커버리지 갭.

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| (요약 줄) | 남은 건수·승인·반려·중복·invalid | 목록 상단 | 결정할 때마다 갱신. 탭 3 배지와 같은 값 | — | — | — | F5.5 |
| `review-filter` | 전체 / 미검토 / 중복 후보 / invalid | 목록 상단 세그먼트 | 클릭 → 카드 필터 | 선택 보라 | — | `GET /api/tc-library/{suite}?status=draft&job_id=…` | F5.5 |
| `review-approve-clean` | 문제없는 초안 일괄 승인 | 목록 상단 오른쪽 | 클릭 → 중복 후보·invalid·추정 문구가 **없는** 미검토 초안만 승인. 토스트에 남겨 둔 건수와 이유 | 대상 0건이면 disabled | — | `POST /api/tc-library/{suite}/bulk` field:"status" value:"approved" | F5.5, 성공 지표 |
| `draft-list` | 초안 카드 목록 | 왼쪽 | — | 비었으면 "검토할 초안이 없습니다. 새로 생성에서 초안을 만드세요" | — | — | F5.5 |
| `draft-card` | 초안 카드 | 목록 | 클릭 또는 J/K → 포커스(보라 테두리), 오른쪽 원문에서 해당 문장 강조 + 스크롤. 사전 조건 / Test Step / Expected / 우선·AUTO 표시. 결정된 카드는 흐려짐 | 포커스 / 승인(60% 불투명) / 반려(45%) / 중복(노랑 테두리) / invalid(빨강 점선) | — | — | F5.5 |
| `draft-source-ref` | 출처 칩 | 카드 오른쪽 위 | 클릭 → 카드 포커스와 원문 강조 | — | 케이스마다 source_ref 정확히 1개 | — | F4.5, 목표 5 |
| `draft-approve` | 승인 | 카드 하단 | 클릭 또는 A → approved, 다음 카드로 포커스, 되돌리기 토스트 | disabled: invalid이거나 중복 처리 미선택(툴팁에 사유) | — | `PATCH /api/tc-library/{suite}/cases/{case_id}` `{rev, status:"approved"}` | F5.5 |
| `draft-reject` | 반려 | 카드 하단 | 클릭 또는 R → rejected, 다음 카드 | — | — | `PATCH …` `{rev, status:"rejected"}` | F5.5 |
| `draft-edit` | 편집 | 카드 하단 | 클릭 또는 E → 라이브러리 탭 상세 패널로 이 케이스 열기 | — | — | — | F5.5 |
| `draft-regen` | 재생성… | 카드 하단 | 클릭 또는 G → 카드 안에 메모 입력칸 펼침 | — | — | — | F5.5 |
| `draft-regen-note` | 재생성 메모 | 카드 안 | 입력(예: "배너 3개일 때와 5개일 때를 행으로 나눠 주세요") | — | 빈 메모 금지(오류 토스트) | — | F5.5 |
| `draft-regen-submit` | 이 메모로 재생성 | 메모 아래 | 클릭 → 이 케이스만 다시 생성, 이전 초안은 이력에 남김 | loading("재생성 중…") / 다른 작업 진행 중이면 대기열 표시 | 1건 제한과의 관계는 9장 #11 | `POST /api/tc-library/{suite}/jobs` `{mode:"regenerate", case_ids:[…], note}` | F5.5, F4.1 |
| `draft-regen-cancel` | 닫기 | 메모 아래 | 메모 칸 접기 | — | — | — | — |
| `dup-resolution` | 중복 후보 상자 | 중복 카드 안 | "기존 케이스와 비슷합니다 · BEN_0002 (92%)" + 기존/초안 나란히 비교 | 노랑 배경 | 같은 기능 가지 안 Step+Expected 유사도 기준 | 초안 응답의 `duplicate_of:{case_id, similarity}` | F5.6 |
| `dup-update` | 기존 케이스 갱신 | 중복 상자 세그먼트 | 선택 → 승인 버튼 활성. 승인 시 기존 case_id에 초안 내용을 덮고 초안은 삭제 | 선택 보라 | 기존 케이스의 rev 동봉 | `POST /api/tc-library/{suite}/cases/{draft_id}/resolve-duplicate` `{action:"update", target_case_id, target_rev}` | F5.6 |
| `dup-skip` | 건너뛰기 | 동일 | 선택 → 초안을 반려 처리 | — | — | 동일 `{action:"skip"}` | F5.6 |
| `dup-add` | 새로 추가 | 동일 | 선택 → 승인 버튼 활성. 별도 케이스로 승인 | — | — | 동일 `{action:"add"}` | F5.6 |
| `source-tabs` | Confluence / Figma 원문 탭 | 오른쪽 위 | 클릭 → 원문 종류 전환 | — | 포커스된 카드의 출처 종류로 자동 전환 | — | F5.5 |
| `source-excerpt` | 원문 발췌 | 오른쪽 | 섹션 제목(§2.1 등)과 본문. 초안 근거 문장은 노랑 하이라이트, 포커스된 카드의 근거는 보라 배경 | loading / error("원문을 불러오지 못했습니다") | 번들의 `NN_{slug}.md`에서 읽음(원본 재요청 안 함) | `GET /api/tc-library/sources/{bundle}/excerpt?ref=conf:48213377@v14&anchor=§2.1` → `{markdown, highlights:[{start,end,case_id}]}` | F5.5 |
| `source-open-original` | 원본 열기 | 발췌 위 | 링크 → 새 탭에서 Confluence 원본 | — | 서버가 조립한 URL만 사용 | — | F1.3 |
| `source-figma-frame` | Figma 프레임 | Figma 탭 | 프레임 PNG(번들 `assets/`), 아래 프레임 이름·TEXT 수·variant. 좌우 넘김으로 프레임 전환 | 이미지 없음 → 회색 자리 + "프레임 이미지를 받지 못했습니다" | 최대 10장 | `GET /api/tc-library/sources/{bundle}/assets/{file}.png` | F1.4, F5.5 |
| `coverage-gap` | 커버리지 갭 | 오른쪽 아래 | 기능마다 프로필 규칙 대비 충족 여부 막대(초록=충족, 빨강=부족)와 부족한 이유 | — | 프로필 규칙: 정상 ≥1, 예외 ≥1, 입력 필드면 유효성 ≥1 | `GET /api/tc-library/{suite}/coverage?path=…&profile=…` | F5.10 |
| `coverage-generate-more` / `coverage-generate-more-2` | 예외 생성 / 생성 | 갭 항목 오른쪽 | 클릭 → 새로 생성 탭으로 이동, 대상 가지와 메모("예외 케이스: 링크 없음, 만료 링크")를 채워 둠 | — | — | — | F5.10 |

---

## 5. 내보내기 (F6, F7)

### 5.1 엑셀로 내보내기

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `xlsx-scope` | 범위 라디오 | 엑셀 카드 | 전체 / 선택한 시트 / 현재 필터 결과 / 승인된 케이스만. 각 항목 옆 건수. 바꾸면 검사 결과 초기화, 내려받기 disabled | 선택 보라 | "현재 필터 결과"는 라이브러리 필터를 그대로 사용 | — | F6.1 |
| `xlsx-sheets` | 시트 선택 | "선택한 시트" 옆 | 선택 | — | — | — | F6.1 |
| `xlsx-openpyxl-warning` | 저장 손실 경고 | 엑셀 카드 | 템플릿 분석 때 센 조건부서식·이미지·차트 수와 손실 위험 | 노랑 | — | template_profile 값 | F2.6 |
| `xlsx-run-check` | 검사 실행 | 무결성 검사 영역 | 클릭 → 서버가 사본에 쓰고 다시 열어 검사. 결과 목록 표시, 성공 시 내려받기 활성 | loading("사본에 쓰고 다시 여는 중…") / error(✕ 항목이 있으면 내려받기 disabled) | 항상 원본이 아닌 사본 | `POST /api/tc-library/{suite}/export/xlsx` `{scope, sheets?, filter?, history_note, dry_run:true}` → `{export_id, checks:[{ok, level, text}]}` | F6.2, F6.3, F6.6 |
| `xlsx-integrity` | 검사 결과 목록 | 무결성 검사 영역 | 계층 트리 일치, No. 수식, 병합, 드롭다운 범위, 요약 수식 재작성(`#REF!` 교정 건), 소문자 `average()` 주의, History 행 추가 | ✓ 초록 / ! 노랑(내려받기 가능) / ✕ 빨강(불가) | — | 위 응답 | F6.2~F6.6, O5 |
| `xlsx-history-note` | History 시트 행 | 엑셀 카드 | 기본값 자동 작성(날짜 `YY.MM.DD`, 소스 목록, 추가·수정 건수), 사용자 편집 가능 | — | 비우면 기본값 사용 | 요청 `history_note` | F6.4 |
| `xlsx-filename` | 파일 이름 미리보기 | 엑셀 카드 | `{원본}_{YYYYMMDD_HHMM}.xlsx` | — | 파일명은 서버가 확정 | — | F6.6 |
| `xlsx-download` | 내려받기 | 엑셀 카드 하단 | 검사 성공 후 활성 → 파일 저장 | 검사 전·실패 시 disabled("검사 후 내려받기") / loading | 검사 후 라이브러리가 바뀌었으면 다시 검사 요구(export_id 만료) | `GET /api/tc-library/exports/{export_id}/download` | F6.6 |

### 5.2 md로 내보내기

| 요소 ID | 요소 | 위치 | 동작(트리거→결과) | 상태 | 검증·제약 | API 호출 | 관련 PRD |
|---|---|---|---|---|---|---|---|
| `md-eligibility` | 대상 조건 퍼널 | md 카드 | 라이브러리 전체 → AUTO=Y-web → 승인됨 → 추정 문구 없음 → pages.json 매핑됨. 막대 길이는 전체 대비 비율, 마지막 단계 초록 | — | — | `GET /api/tc-library/{suite}/export/md/eligibility` → `{total, y_web, approved, no_estimated, mapped}` | F7.1 |
| `md-group-map` | 그룹 매핑 목록 | md 카드 | 가지 → 그룹코드와 `config/pages.json` 매핑 여부. 매핑 없으면 빨강 "URL 없음 · n건 제외" | — | — | 위 응답 `groups[]` | F7.1, F7.3 |
| `md-map-fix` | 매핑 추가 | 매핑 없는 행 | 클릭 → 대시보드 페이지 관리 화면(pages.json 편집)으로 이동 | — | — | — | F7.1 |
| `md-drift-warning` | 직접 수정된 파일 경고 | md 카드 | `testcases/`에서 마지막 내보내기 이후 바뀐 파일 목록. 미리보기에서 각 충돌의 처리 방법을 고르도록 안내 | 노랑 | 해시 비교 | 위 응답 `drifted_files[]` | F7.5 |
| `md-excluded-list` | 제외된 n건 보기 | md 카드 | 펼치면 제외 사유별 목록(추정 / 미승인 / 매핑 없음). 항목 클릭 → 라이브러리 상세 | — | — | 위 응답 `excluded[]` | F7.1 |
| `md-preview` | md 미리보기 (n건) | md 카드 하단 | 클릭 → 서버가 변환·검증 후 같은 화면의 `md-preview-panel`을 펼침 | 대상 0건 disabled / loading / error(검증 실패 건 목록) | 파일명 `tc_{그룹코드}_{번호}_{english_snake_case}.md`, P0 → very_high, P1 → high, P2 → medium, P3 → low (PRD O7 선행), `source_ref` 한 줄 | `POST /api/tc-library/{suite}/export/md` → `{preview_id, count, conflicts}` (내부에서 `create_preview_from_rows`) | F7.2~F7.4 |
| `md-preview-panel` | 신규·갱신·동일·충돌·오류 결과 | md 카드 하단 | 미리보기 작업 ID와 건별 대상 파일·변경 내용 표시. 상태별 필터와 제외 건 목록 제공 | 미리보기 전 숨김 | 라이브러리/대상 파일이 바뀌면 재미리보기 필요 | `GET /api/tc-library/md-exports/{preview_id}` | F7.6 |
| `md-conflict-decision` | 충돌 건 처리 | 미리보기 패널 | 각 충돌에서 건너뛰기 또는 덮어쓰기 선택 → 커밋 가능 여부 갱신 | 미결정이면 커밋 disabled | 직접 수정된 내용 비교 후 결정 | 커밋 요청 `decisions[]` | F7.5, F7.6 |
| `md-commit` / `md-rollback` | md 파일 반영·되돌리기 | 미리보기/결과 패널 | 커밋 → `testcases/` 반영·결과 표시. 롤백 → 해당 작업의 스냅샷 복구 | 진행 중 loading / 충돌 시 error | 작업 ID·멱등 키·대상 변경 재검사, 롤백 전 변경 검사 | `POST /api/tc-library/md-exports/{preview_id}/commit`, `POST /api/tc-library/md-exports/{preview_id}/rollback` | F7.6 |

---

## 6. 키보드 단축키

| 범위 | 키 | 동작 |
|---|---|---|
| 전역 | `Esc` | 열린 모달 닫기 → 셀 편집 취소 → 선택 해제 순서 |
| 라이브러리 | `/` | 검색칸 포커스 |
| 라이브러리 | `↑` `↓` | 그리드 활성 행 이동(상세 패널 따라 바뀜) |
| 라이브러리 | `←` `→` / `Tab` | 셀 이동 |
| 라이브러리 | `Enter` | 포커스된 셀 편집 시작 |
| 라이브러리 셀 편집 | `⌘/Ctrl + Enter` | 셀 저장 |
| 라이브러리 셀 편집 | `Enter` | 줄바꿈(사전 조건·Step·Expected) |
| 라이브러리 | `Space` | 활성 행 선택 토글 |
| 라이브러리 | `Shift + 클릭` | 범위 선택 |
| 라이브러리 | `⌘/Ctrl + A` (그리드 포커스 시) | 필터 결과 전체 선택 |
| 상세 패널 | `⌘/Ctrl + S` | 저장 |
| 상세 패널 Step | `Alt + ↑/↓` | Step 순서 이동 |
| 상세 패널 Step | `Enter` | 아래에 새 Step |
| 트리 | `Enter` / `Space` | 펼침·선택 |
| 초안 검토 | `J` / `K` | 다음 / 이전 카드 |
| 초안 검토 | `A` | 승인 |
| 초안 검토 | `R` | 반려 |
| 초안 검토 | `G` | 재생성 메모 열기 |
| 초안 검토 | `E` | 라이브러리에서 편집 |

입력칸·편집 중인 셀에서는 한 글자 단축키(J/K/A/R/G/E, /)가 동작하지 않는다.

## 7. 빈 상태와 오류 상태 모음

| 상황 | 표시 | 복구 동작 |
|---|---|---|
| 라이브러리 0건 | `lib-empty`: "야핏무브 라이브러리가 비어 있습니다" + 엑셀 가져오기 / 문서로 새로 생성 | 가져오기 모달 |
| 필터 결과 0건 | `grid-empty-filter`: "조건에 맞는 케이스가 없습니다" | 필터 초기화 |
| 소스 0개 | `src-list`: "아직 수집한 소스가 없습니다", `gen-submit` disabled | 소스 추가 |
| 자격증명 없음 | 연결 태그 회색, 수집 버튼 disabled, 툴팁 "연결 설정에서 토큰을 등록하세요" | `cred-settings` |
| 수집 실패 | 소스 카드 빨강 태그(403 권한 없음 / 404 페이지 없음 / 허용되지 않은 호스트 / 20MB 초과 / 시간 초과 15초) | 카드 제거 후 다시 수집 |
| 업로드 초과 | 413 → "25MB를 넘습니다" / "PDF는 200쪽까지만 받습니다" | 파일 줄이기 |
| 생성 작업 실패 | 실패 박스 + 로그 끝부분 + 살린 초안 수 | `job-retry`, `job-open-review-partial` |
| `claude` CLI 없음 | 실패 박스: "claude 명령을 찾지 못했습니다. 대시보드를 실행한 셸에서 claude --version이 되는지 확인하세요" | 설치 후 다시 생성 |
| 동시 작업 | `gen-submit` disabled + "다른 생성 작업이 진행 중입니다 (job_…)" | 진행 중 작업으로 이동 |
| rev 충돌 | 자동으로 닫히지 않는 오류 토스트, 내 변경 유지 | 비교 / 최신 값 불러오기 |
| 소스 버전 변경 | `banner-source-changed` + 트리 노랑 점 + 그리드 `재검토 필요` 배지 | 재검토 필터, 변경 확인 완료 |
| 초안 0건 | `draft-list`: "검토할 초안이 없습니다" | 새로 생성으로 |
| 엑셀 검사 실패 | ✕ 항목 + 내려받기 disabled | 원인 케이스 링크로 라이브러리 이동 |
| md 대상 0건 | 퍼널 마지막 0, 미리보기 버튼 disabled, 제외 사유 펼침 | AUTO·승인·추정 문구 정리 |

---

## 8. API 엔드포인트 요약

모든 쓰기 요청은 `_check_csrf_origin` 적용, 요청 크기 상한 초과 시 413. 케이스 쓰기는 `rev`가 필수이며 불일치 시 409와 서버의 최신 케이스를 돌려준다. 서버 쓰기는 `update_state` 원자 패턴을 쓰고 변경마다 `{suite}.history.jsonl`에 한 줄을 추가한다. 케이스 경로에는 스위트가 들어간다 (로드맵 Z2).

| 메서드 | 경로 | 용도 | 주요 응답 | 요소 | PRD |
|---|---|---|---|---|---|
| GET | `/api/tc-library` | 스위트 목록 | `[{suite, sheets, count}]` | `suite-select` | §5 |
| GET | `/api/tc-library/{suite}/tree` | 계층 트리 + 상태 집계 | 트리 노드 배열 | `lib-tree`, `gen-target-*`, `move-target` | F2.2, F5.1 |
| GET | `/api/tc-library/{suite}` | 케이스 목록(필터·검색·페이지) `?sheet&path&status&execution_result&priority&auto&source&needs_review&invalid&q&offset&limit` | `{items, total}` | `lib-grid`, 필터 전부 | F5.1, F5.4 |
| POST | `/api/tc-library/{suite}/cases` | 케이스 추가 | 새 케이스 | `btn-add-case` | F5.3 |
| GET | `/api/tc-library/{suite}/cases/{case_id}` | 케이스 1건 | 케이스 + validation | `detail-panel` | F5.1 |
| PATCH | `/api/tc-library/{suite}/cases/{case_id}` | 필드 수정 `{rev, …}` | 200 케이스 / 409 `{server_case}` | 셀 편집, `detail-save`, 검토 승인·반려 | F5.2, F5.5 |
| DELETE | `/api/tc-library/{suite}/cases/{case_id}?rev=` | 삭제 | 204 / 409 | `detail-delete` | F5.3 |
| POST | `/api/tc-library/{suite}/cases/{case_id}/duplicate` | 복제 | 새 케이스 | `detail-duplicate` | F5.3 |
| POST | `/api/tc-library/{suite}/bulk` | 일괄 set/duplicate/delete `{items:[{case_id,rev}], op, field, value}` | `{updated, conflicts}` | `bulk-*`, `review-approve-clean` | F5.3 |
| POST | `/api/tc-library/{suite}/move` | 계층 이동 | `{moved, conflicts}` | `move-confirm`, 트리 드롭 | F5.3 |
| GET | `/api/tc-library/{suite}/cases/{case_id}/history` | 변경 이력 | 이력 배열 | `detail-history` | F5.11 |
| POST | `/api/tc-library/{suite}/cases/{case_id}/revert` | 이전 값으로 되돌리기 `{history_id, rev}` | 케이스 | `detail-history-revert`, 되돌리기 토스트 | F5.11 |
| POST | `/api/tc-library/{suite}/cases/{case_id}/resolve-duplicate` | 중복 처리 `{action, target_case_id, target_rev}` | 결과 케이스 | `dup-*` | F5.6 |
| POST | `/api/tc-library/{suite}/source-changes/scan` | 원격 버전 확인·표시 | `{checked, changes, errors}` | `btn-check-sources` | F5.9 |
| GET | `/api/tc-library/{suite}/source-changes` | 소스 버전 변화와 영향 케이스 | `[{ref, from, to, case_ids}]` | `banner-source-changed` | F5.9 |
| POST | `/api/tc-library/{suite}/cases/{case_id}/ack-source` | 새 소스 버전 확인 `{ref, to_version, rev}` | 케이스 | `detail-mark-reviewed` | F5.9 |
| GET | `/api/tc-library/{suite}/coverage` | 커버리지 갭 `?path&profile` | 기능별 충족 여부 | `coverage-gap` | F5.10 |
| POST | `/api/tc-library/import/preview` | xlsx 분석(multipart) | `{preview_id, header_row, sheets, warnings}` | `import-modal` | F2.1~F2.3, F2.6 |
| POST | `/api/tc-library/import` | 가져오기 확정 `{preview_id, sheets}` | `{created, updated, skipped}` | `import-confirm` | F2.4, F6.7 |
| POST | `/api/tc-library/{suite}/export/xlsx` | 사본 생성·무결성 검사 `{scope, …, history_note, dry_run}` | `{export_id, checks, filename}` | `xlsx-run-check` | F6.1~F6.6 |
| GET | `/api/tc-library/exports/{export_id}/download` | 파일 내려받기 | xlsx | `xlsx-download` | F6.6 |
| GET | `/api/tc-library/{suite}/export/md/eligibility` | md 대상 퍼널·매핑·드리프트 | `{funnel, groups, drifted_files, excluded}` | `md-*` | F7.1, F7.5 |
| POST | `/api/tc-library/{suite}/export/md` | 변환·검증 후 Studio 내부 미리보기 생성 | `{preview_id, count, conflicts}` | `md-preview` | F7.2~F7.4 |
| GET / POST | `/api/tc-library/md-exports/{preview_id}` 및 `/commit`, `/rollback` | 미리보기 조회·충돌 결정 후 커밋·롤백 | `{rows, summary, snapshot_id?, result?}` | `md-preview-panel`, `md-commit`, `md-rollback` | F7.6 |
| GET / PUT | `/api/tc-library/import/profiles`, `/api/tc-library/import/profiles/{name}` | 기존 Excel 매핑 프로필 조회·저장 | 프로필 목록·매핑 | `import-mapping-profile` | F2.1, D6 |
| POST | `/api/tc-library/sources/{bundle}/{kind}` | 소스 1개 수집(file/paste/url/confluence/figma) | manifest 항목 `{source_id, kind, ref, version, chars, images, truncated}` | `src-*-fetch`, `src-file-drop`, `src-paste-add` | F1.1~F1.6 |
| DELETE | `/api/tc-library/sources/{bundle}/{source_id}` | 소스 제거 | 204 | `src-chip-remove` | F1.5 |
| GET | `/api/tc-library/sources/{bundle}/excerpt` | 번들 발췌 + 하이라이트 `?ref&anchor` | `{markdown, highlights}` | `source-excerpt`, 상세 `원문` 탭 | F5.5 |
| GET | `/api/tc-library/source-diff` | 소스 버전 간 바뀐 문장 `?ref&from&to` | diff 블록 | `banner-diff`, 원문 탭 | F5.9 |
| GET | `/api/tc-library/credentials` | 연결 상태 | `{confluence:{configured, base_url, email_masked}, figma:{configured}}` | `cred-status-*` | §7 |
| PUT | `/api/tc-library/credentials/{kind}` | 자격증명 저장 | 위와 같은 마스킹 응답 | `cred-settings` | §7 |
| GET / PUT | `/api/tc-library/profiles`, `/api/tc-library/profiles/{name}` | 작성 프로필 목록·저장 | 프로필 | `gen-profile`, `gen-profile-edit` | F3 |
| POST | `/api/tc-library/{suite}/jobs` | 생성 작업 시작(신규 / 재시도 / 케이스 재생성) | `{job_id}` / 409 진행 중 | `gen-submit`, `job-retry`, `draft-regen-submit` | F4.1~F4.5 |
| GET | `/api/tc-library/jobs/{id}` | 작업 상태(`status.json`) | `{status, step, sections, kept, invalid, reason}` | `job-panel` | F4.4 |
| POST | `/api/tc-library/jobs/{id}/cancel` | 작업 취소 | 200 | `job-cancel` | F4.1 |
| GET | `/api/tc-library/jobs/{id}` | 로그 `?tail=` | 텍스트 | `job-log-tail`, `job-log-full` | F4.6 |
| GET | `/api/tc-library/sources/{bundle}/assets/{file}` | Figma 프레임 PNG | image/png | `source-figma-frame` | F1.4 |
| 폴링 | 1.5초 폴링 (Phase 2 결정 Y3) | 생성 작업 진행률 | — | `job-progress`, 배너, 그리드 새로고침 | F4.4 |

---

## 9. PRD 피드백

실제 `야핏무브_Full.xlsx`(읽기 전용)를 열어 확인한 내용과 화면을 설계하며 드러난 빈틈이다.

1. **AUTO 드롭다운 값이 PRD와 다르다.** 모든 TC 시트의 J열 데이터 유효성 허용값은 `"AUTO"` 한 가지뿐이다(예: 혜택 `J13:J198`). `Y-web/Y-app/N`을 쓰면 기존 드롭다운 규칙을 어긴다. F6.2의 "드롭다운 범위를 넓힌다"만으로는 부족하고, 목록 값 자체를 바꿀지 정해야 한다(O4와 묶어서 결정).
2. **`platforms` 필드의 근거가 없다.** K/L(And/iOS)은 플랫폼 속성이 아니라 결과 컬럼이다(허용값 `Pass,Fail,NT,NA`). 플랫폼 한정 정보는 사전 조건 텍스트에 있다(홈 시트 "- only And"). §5 표의 `platforms` = "K/L 헤더"는 F2.4("결과 컬럼 K/L은 가져오지 않는다")와 충돌한다. 필드를 빼거나 사전 조건에서 뽑는 규칙을 정해야 한다.
3. **우선순위·AUTO가 전 시트에서 비어 있다.** F2.4대로 926건을 `approved`로 가져오면 F5.8 "허용된 우선순위" 검증에서 926건 모두 오류가 된다. 빈 값을 오류로 볼지 경고로 볼지 정해야 한다. 목업은 "미지정 = 노랑 경고, 승인 차단 안 함"으로 가정했다.
4. **헤더 자동 탐지 기준이 필요하다.** 1~9행에 요약표("구분 / COUNT / 수행률", "And / iOS")가 있어 헤더 후보가 여럿이다. "No.·기능·Expected Result를 모두 포함한 첫 행" 같은 판정 기준을 F2.1에 적어야 한다.
5. **기타 컬럼에 사람이 쓴 메모가 이미 있다.** 혜택 R16 "돈불리기 정책 변경 (신규 온보딩 추가 필요)". F6.5의 `id:… | src:…`를 같은 칸에 쓰면 메모와 섞인다. 재가져오기(F6.7) 때 메모와 추적 정보를 나누는 규칙이 필요하고, 라이브러리 모델에 `note` 필드가 필요하다.
6. **`source_refs[]`(배열), F4.5 "정확히 1개", md의 단일 `source_ref`가 서로 어긋난다.** 수동 편집으로 출처를 여러 개 연결하면 md에 무엇을 쓸지 정해야 한다. 엑셀에서 가져온 케이스의 출처 표기(`xlsx:파일#시트!행`?)도 §5에 정의가 없다.
7. **`needs_review`를 status 값으로 두면 원래 상태를 잃는다.** approved 케이스가 재검토로 바뀌었다가 해제되면 approved로 돌아가야 하는지 draft로 돌아가야 하는지 알 수 없다. `status`와 별개의 `needs_review` 플래그(+ 바뀐 ref/버전)를 권한다. 해제 조건(내용 수정 없이 "확인"만으로 해제 가능한지)도 정해야 한다. 목업은 별도 플래그 + `변경 확인 완료` 버튼으로 설계했다.
8. **반려된 케이스의 처리 규칙이 없다.** 라이브러리에 남는지, 엑셀 내보내기 "전체"에 들어가는지, 재생성하면 어떻게 되는지 정해야 한다. 목업은 "남아 있고, 엑셀 전체에서는 제외"를 가정했다.
9. **중복 "기존 케이스 갱신"의 결과가 정의되지 않았다.** 기존 approved 케이스가 draft로 돌아가는지, case_id와 이력은 유지되는지 적어야 한다.
10. **F1.6과 F4.4가 수집 시점을 다르게 본다.** F1.6은 생성 전에 수집 결과를 보여 달라고 하는데 F4.4의 작업 단계에는 `fetching`이 들어 있다. 수집을 별도 API(`POST /api/tc-library/sources/{bundle}/{kind}`)로 먼저 하고, 작업의 fetching은 번들 확정·버전 재확인 단계로 두기를 제안한다.
11. **"한 번에 1건"(F4.1)과 카드 단위 재생성(F5.5)의 관계가 없다.** 검토 중 재생성을 여러 번 누르면 큐에 쌓는지 거부하는지 정해야 한다. 작업 취소 시 이미 나온 초안을 살릴지도 빠져 있다.
12. **삭제와 되돌리기 범위가 모호하다.** F5.11은 필드 단위 되돌리기인데 삭제된 케이스 복원 경로가 없다. 삭제한 case_id가 있는 엑셀을 다시 가져올 때(F6.7) 되살릴지 무시할지도 정해야 한다.
13. **계층 가지 자체의 편집이 요구사항에 없다.** 새 중분류 추가, 가지 이름 변경, 빈 가지 삭제가 필요하다. 생성 대상 선택(시나리오 2 "혜택 › 상단 배너")에서도 없는 가지를 만들 수 있어야 한다.
14. **md 그룹 매핑 규칙이 없다.** F7.1의 "그룹"이 시트인지, 대분류인지, 중분류인지, 그리고 그룹코드(`tc_{그룹코드}_…`)를 어떻게 만드는지 정해야 한다. 목업은 "중분류 → 그룹코드, 사용자가 매핑 추가"로 가정했다.
15. **일괄 편집 중 일부만 충돌할 때의 정책이 없다.** 전부 실패인지 부분 성공인지 정해야 한다. 목업은 부분 성공 + 충돌 건 안내로 설계했다.
16. **결과 컬럼을 비우면 실행 기록이 사라진다.** F6.5는 새 파일에서 K/L을 비운다. 원본에 Pass/Fail 기록이 있으면 그 기록은 새 파일에 남지 않는다. 경고 문구를 넣을지, 결과 보존 옵션을 둘지 정해야 한다.
17. **History 시트 날짜 형식.** 실제 History 시트는 `25.09.11` 같은 `YY.MM.DD` 텍스트다. F6.4에 형식을 적어 두면 좋다.
18. **"출처" 필터(F5.4)의 값 목록이 정의되지 않았다.** 목업은 `xlsx / conf / figma / file` 접두사로 가정했다.
19. **요약 수식은 `#REF!` 말고도 범위가 시트마다 다르게 고정돼 있다.** 혜택은 `COUNTA($A$13:$A$390)`인데 데이터는 198행에서 끝난다. F6.3의 재작성 대상에 COUNTA 범위와 소문자 `average()`(O5)를 함께 적어 두기를 제안한다.
