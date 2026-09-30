# Lessons Learned — QA 자동화 실수 패턴

> **독자**: 심의 Agent — 코드 작성·리뷰·힐링 전 자동 참조.
> 같은 실수를 반복하지 않기 위한 **큐레이션된** 패턴 모음.
> 자동 기록 로그는 [lessons_learned_auto.md](lessons_learned_auto.md) 참조.
> **관리 규칙**: 중복 섹션 발견 즉시 병합. Stale 패턴 삭제. 500줄 이상 시 큐레이션 패스 실행.

---

### [수정] 2026-09-07 -- Import Studio 카드 레이아웃
- **문제**: 단계 바를 전체 폭으로 확장하면서 루트 컨테이너까지 화면 전체 높이로 늘어나, 콘텐츠가 적어도 하단 액션 바가 뷰포트 바닥에 붙었다.
- **재발 방지**: 단계 연결선만 남는 가로폭을 유연하게 분배하고, Studio 루트는 공통 콘텐츠 여백 안에서 내용 높이를 따르는 카드로 유지한다.

### [수정] 2026-09-05 -- 리포트 관리 UI
- **문제**: 파일명을 인라인 JavaScript 문자열에 삽입하면 따옴표가 이벤트 코드를 깨뜨리고, URL 인코딩 없이 리포트를 열면 특수문자가 경로로 잘못 해석될 수 있다.
- **재발 방지**: 파일명은 이스케이프한 data 속성과 이벤트 리스너로 전달하고, 요청 경로는 encodeURIComponent로 인코딩한다. 서버는 경로를 한 번 디코딩한 뒤 파일명·경로 경계를 검증한다. 한글·따옴표·HTML 특수문자 파일명으로 실제 브라우저 미리보기·새 탭·삭제를 검증한다.
- **선택 삭제**: 모든 파일명을 삭제 전에 검증하고, 기존 리포트를 건드리지 않는 임시 디렉터리에서 보안·누락·성공 경로를 테스트한다.
- **검색 입력**: input 이벤트마다 DOM을 교체하는 화면에서는 isComposing 동안 재렌더링하지 않고 compositionend에서 검색을 반영해 한글 조합을 보존한다. 열기·닫기·페이지 이동 후 키보드 포커스도 복원한다.

### [수정] 2026-09-01 -- parallel/99_merge.py
- **문제**: `argparse`에 `--no-report` 인자가 누락되어 `AttributeError: 'Namespace' object has no attribute 'no_report'` 발생. 테스트는 전부 통과했지만 스크립트가 크래시됨.
- **수정**: `parser.add_argument("--no-report", action="store_true", ...)` 추가.
- **재발 방지**: 99_merge.py에 새 CLI 플래그를 추가할 때 argparse 선언과 `args.{flag}` 사용 위치를 함께 검색해 누락 여부 확인. 새 플래그 추가 후 반드시 `python parallel/99_merge.py --help`로 등록 확인.

### [수정] 2026-09-01 -- tests/generated/customer_login/tc_02_wrong_credentials_error.py
- **문제**: 힐링 과정에서 `assert any(keyword in msg_text.lower() for keyword in error_keywords)`가 `assert msg_text`로 약화됨. assertion 무결성 경고 발생 (9→7개).
- **수정**: `assert msg_text` → `assert any(keyword in msg_text.lower() for keyword in error_keywords)` 로 복원. 키워드 목록은 dialog 분기에서 사용하는 동일 리스트 사용.
- **재발 방지**: 힐링 패치 후 assertion 무결성 경고가 뜨면 반드시 원본 assertion 강도를 복원할 것. `assert <텍스트>` 단순 비어있지않음 체크는 키워드·상태 조건 체크를 대체할 수 없음.

### [수정] 2026-09-30 -- TC Studio 계획의 단계별 import
- **문제**: B6 테스트가 B7에서 정의할 verify_export를 미리 import해 B6 통과 확인이 불가능했다.
- **재발 방지**: 검증 함수를 사용하는 작업에서 import를 추가한다. B6/B7 assertion은 그대로 유지한다.

### [수정] 2026-09-30 -- TC Studio W2 테스트 블록 누락
- **문제**: Phase 1 W2의 테스트 코드 블록이 비어 있어 예상한 E2E 7개를 구성할 수 없었다.
- **재발 방지**: 명세의 빈 화면→미리보기→시트별 접두어→가져오기→재로딩 유지 흐름을 E2E로 보완하고 버튼 부재 실패를 먼저 확인했다.

### [수정] 2026-09-30 -- TC Studio 폴링 중 편집 상태 보존
- **문제**: 공통 refreshAll/SSE가 스튜디오를 재렌더해 실제 엑셀 미리보기·모달·미저장 편집을 지웠다.
- **재발 방지**: 자체 상태를 관리하는 TC Studio를 Import Studio와 같이 _shouldSkipRender에서 제외한다. refreshAll 후 모달 DOM·표시 보존을 E2E로 검증한다.

### [수정] 2026-09-30 -- Phase 2 화면 테스트 선행 의존·누락
- **문제**: W5 테스트가 W6에서 추가되는 검토 화면·배지를 먼저 요구하고 W6 테스트 블록은 비어 있다.
- **재발 방지**: 생성 완료 검증은 W5에서 수행하고 기존 배지·검토 카드 검증은 W6로 이동한다. W6에서 원문 하이라이트·승인·반려·되돌리기·재생성 E2E 두 개를 추가한다. 검증을 삭제하거나 약화하지 않는다.

### [수정] 2026-09-30 -- 재생성 후 검토 목록 유지
- **문제**: 재생성이 draft_meta.job_id를 덮어써 원래 작업의 검토 목록에서 카드가 사라졌다. W6 재생성 E2E에서 RED 확인.
- **재발 방지**: 원래 생성 작업 ID는 유지하고 regenerated_job_id에 재생성 작업을 기록한다. 재생성 후 같은 case_id·카드 2건 유지 및 승인 가능 검증을 그대로 통과시킨다.
