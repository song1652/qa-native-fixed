# 코드 리뷰 프롬프트 (03a_dialog.py 후 사용) — P64 업데이트

> 페르소나 시뮬레이션 제거. Claude Code가 체크리스트 기반으로 직접 코드를 리뷰·수정한다.
> `{ctx.*}` 참조는 DELIBERATION_CONTEXT JSON의 해당 키를 의미한다.
> Playwright 코드 규칙: `.claude/skills/playwright-best-practices/SKILL.md` 참조.

아래 컨텍스트를 바탕으로 코드 리뷰를 수행하고 필요 시 코드를 직접 수정하라.

lessons_learned: {ctx.lessons_learned}
generated_code: {ctx.generated_code}
lint_result: {ctx.lint_result}
plan: {ctx.plan}

## 실행 순서

1. **lessons_learned 확인** — 과거 Assertion/Locator 오류 패턴과 현재 코드 대조. 동일 패턴 발견 시 즉시 수정
2. **lint 이슈 수정** — 있는 경우 해당 `tests/generated/{group}/*.py` 파일 직접 편집
3. **체크리스트 검토** — 아래 필수 항목 순서대로 확인 후 문제 있으면 수정
4. **state/pipeline.json에 review_summary 저장**, step = "reviewed"
5. **새 실수 패턴 발견 시** `agents/lessons_learned.md` 해당 섹션에 한 줄 추가 (중복 시 생략)

## 필수 검토 체크리스트

| 항목 | 기준 | 심각도 |
|------|------|--------|
| 공유 헬퍼 금지 | helpers.py 등 외부 파일 import → 각 파일 자체 완결 | CRITICAL |
| test_data 경로 | `Path(__file__).resolve().parent` 4번 → 프로젝트 루트 (3번 아님) | HIGH |
| 함수명 영문 | `test_{english_snake_case}` 형식 (한글 금지) | HIGH |
| 셀렉터 안정성 | id 기반 우선, 클래스 추측 금지 | HIGH |
| dialog 핸들러 | conftest fixture 중복 방지 — message append only | MEDIUM |
| to_contain_text | `to_have_text` 대신 사용 (공백 포함 가능성) | MEDIUM |
| ENV 미처리 | `os.environ.get()` + 미설정 시 `pytest.skip()` | MEDIUM |
| 미사용 import | 제거 | LOW |

## Few-shot 예시 (참조용)

코드 리뷰 good/bad 예시: `prompts/examples/review_good_bad.json`
