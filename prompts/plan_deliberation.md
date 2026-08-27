# Plan 생성 프롬프트 (02a_dialog.py 후 사용) — P64 업데이트

> 페르소나 시뮬레이션 제거. Claude Code가 컨텍스트를 직접 분석하여 plan을 생성한다.
> `{ctx.*}` 참조는 DELIBERATION_CONTEXT JSON의 해당 키를 의미한다.

아래 컨텍스트를 바탕으로 테스트 plan을 생성하라.
사수/부사수 역할극 없이, lessons_learned 확인 → dom_info+test_cases 분석 → plan 직접 출력 순으로 진행한다.

lessons_learned: {ctx.lessons_learned}
dom_info: {ctx.dom_info}
sub_doms: {ctx.sub_doms}
test_cases: {ctx.test_cases}

## 실행 순서

1. **lessons_learned 확인** — 이 URL·셀렉터와 관련된 과거 실수 패턴을 먼저 확인하고, 있으면 plan에 반영한다
2. **dom_info 분석** — 셀렉터 우선순위: id > testid > aria_label > name > css. 불안정한 클래스 기반 셀렉터는 id로 대체
3. **test_cases → plan 변환** — 각 케이스의 precondition/steps/expected를 plan 스키마로 직접 변환
4. **state/pipeline.json에 plan 저장**, step = "planned"

## plan 항목 JSON 스키마

```json
{
  "case_name": "tc_{번호}_{english_snake_case}",
  "case_type": "structured | natural",
  "description": "테스트 목적을 구체적으로 기술 (모호한 표현 금지)",
  "steps": [
    {"action": "goto|fill|click|hover|select|wait|evaluate", "selector": "#id 또는 dom_info 기반 셀렉터", "value": "test_data 참조 또는 리터럴"}
  ],
  "assertion": {
    "type": "url_contains|element_visible|text_contains|element_count|class_contains",
    "expected": "기대 결과 (외부 사이트 메시지 하드코딩 금지)"
  }
}
```

- structured 케이스: precondition/steps/expected 직접 반영
- natural 케이스: dom_info 기반 steps/assertion 자동 추론

## Few-shot 예시 (참조용)

good plan 예시: `prompts/examples/plan_good.json` — 셀렉터를 dom_info에서 확인, test_data 참조, 영문 snake_case
bad plan 예시: `prompts/examples/plan_bad.json` — 셀렉터 추측, 하드코딩, 한글 함수명, 모호한 description

## 핵심 규칙 (CLAUDE.md 발췌)

- 테스트 함수명: 반드시 영문 snake_case `test_{english_snake_case}` (한글 제목도 영어 번역)
- tc_*.md 1개 = 테스트 파일 1개 = 테스트 함수 1개
- 테스트 데이터 하드코딩 금지 → config/test_data.json 참조
- lessons_learned에서 동일 패턴 발견 시 반드시 plan에 주의사항 반영
- Playwright 코드 규칙: `.claude/skills/playwright-best-practices/SKILL.md` 참조
