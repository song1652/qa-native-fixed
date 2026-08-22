# 병렬 Subagent 코드 생성 프롬프트 (run_qa_parallel.py 후 사용)

> 이 파일은 병렬 subagent에 대한 행동 지침이다.
> `{ctx.*}` 참조는 PARALLEL_SUBAGENT_CONTEXTS → `subagents[]` 배열의 해당 키를 의미한다.
> 공통 참조 파일은 `shared_context_paths`에 경로가 명시되어 있으며, subagent가 직접 읽는다.

아래 컨텍스트를 바탕으로 Playwright 테스트 코드를 생성하라.

### subagent 고유 데이터 (JSON으로 전달됨)
url: {ctx.url}
dom_info: {ctx.dom_info}
test_cases: {ctx.test_cases}
test_data: {ctx.test_data}
output_path: {ctx.output_path}
batch_info: {ctx.batch_info}
batch_files: {ctx.batch_files}

### 공통 참조 파일 (subagent가 직접 읽기 — JSON에 포함되지 않음)
- lessons_learned: `agents/lessons_learned.md`
- team_charter: `agents/team_charter.md`
- Playwright SKILL: `.claude/skills/playwright-best-practices/SKILL.md`
- **parallel_plan**: `state/parallel_plan.json` ← **공통 사전 심의 결과 (반드시 읽기)**

수행할 작업:
0. **`state/parallel_plan.json` 먼저 읽기** (존재 시): 공통 테스트 전략·주의사항을 확인하고
   이후 모든 단계에 반영한다. (`common_patterns`, `common_cautions`, `group_notes` 참조)
1. **공통 참조 파일을 읽기**: `agents/lessons_learned.md` → 과거 실수 패턴 확인 (같은 실수 반복 금지)
2. 배치 내 **모든 test_cases**와 dom_info를 분석해 테스트 plan 수립
   - structured 케이스: precondition/steps/expected 직접 반영
   - natural 케이스: dom_info 기반 steps/assertion 자동 추론
   - **parallel_plan의 `group_notes[group_dir]`** 항목이 있으면 우선 반영
3. plan 기반으로 완전한 Playwright 테스트 코드 작성 (SKILL.md + lessons_learned + parallel_plan 반영)
   - 배치 내 여러 케이스는 **독립적으로 병렬 작성** 가능 (공유 상태 없음)
   - **`common_cautions`의 모든 주의사항**을 코드에 반영 (SPA 대기, 팝업 처리 등)
4. **tc_*.md 1개 = 테스트 파일 1개 = 테스트 함수 1개** 규칙으로 output_path 디렉토리에 개별 파일 저장
   - 파일명: `tc_{번호}_{english_snake_case}.py` (예: `tc_01_login_success.py`)
   - 단일 파이프라인과 동일한 파일명 규칙

## MUST NOT (절대 금지 -- 위반 시 런타임 에러)
- 공유 헬퍼 파일(helpers.py 등) **생성/import 금지** -> 각 파일이 자체 완결
- conftest.py **재정의 금지** (page fixture 이미 있음)
- 입력값 **하드코딩 금지** -> 반드시 test_data.json에서 읽기
- `ENV:` 프리픽스 데이터는 **리터럴 사용 금지** -> `os.environ.get()` 처리, 미설정 시 `pytest.skip()`

## MUST (필수 준수)
- import: `pytest`, `from playwright.sync_api import expect`, `json`, `re`, `from pathlib import Path`
- `BASE_URL = "{url}"` (모듈 상단 선언)
- `TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"`
- 함수명: `test_{english_snake_case}` (한글 제목도 영어로 번역)
- 파일당 테스트 함수 1개 (tc_*.md 1:1 매핑)
- `page.goto(BASE_URL)`로 시작
- Playwright matcher 규칙은 `.claude/skills/playwright-best-practices/SKILL.md` 준수

## SHOULD (권장)
- 로그인 후 팝업/오버레이: JS evaluate로 `display:none` 강제 숨김
- alert 검증: 특정 메시지 대신 alert 발생 여부만 확인
- `to_have_text` 대신 `to_contain_text` 사용 (공백 대응)
