# 힐링 심의 프롬프트 (06a_dialog.py 후 사용)

> 이 파일은 심의 Agent에 대한 행동 지침이다.
> `{ctx.*}` 참조는 DELIBERATION_CONTEXT JSON의 해당 키를 의미한다.
> 오류 유형별 패치 전략: `.claude/skills/heal-patterns/SKILL.md` 참조.

아래 컨텍스트를 바탕으로 실패를 진단하고 코드를 직접 패치하라.

generated_code: {ctx.generated_code}
heal_context: {ctx.heal_context}
dom_info: {ctx.dom_info}
top_heal_patterns: {ctx.top_heal_patterns}
screenshots: {ctx.screenshots}

## Few-shot 예시 (참조용)

오류 유형별 패치 before/after: `prompts/examples/heal_patch.json`
(Locator, Assertion, JS평가, Timeout, Python런타임 각 1건씩 수록)

수행할 작업:
1. top_heal_patterns(빈출 패턴)를 먼저 확인 → 동일 유형이면 우선 적용
2. 각 failure의 traceback 분석 → `.claude/skills/heal-patterns/SKILL.md` 기준으로 패치
3. 실패한 테스트 파일(tests/generated/{group}/*.py)을 직접 패치
4. **[필수]** agents/lessons_learned.md에 교훈 수동 기록 (자동 로그는 heal_utils.py가 lessons_learned_auto.md에 기록. 누락 시 99_merge.py가 경고)
5. heal_context에 screenshot 경로가 있으면 Read tool로 시각 확인
6. traceback만으로 원인 불명확 시 MCP 시각 검증 (HEALING_GUIDE.md 참조)

## 힐링 완료 체크리스트 (하나라도 빠지면 미완료)

> 상세 기준: `doc/operations/HEALING_GUIDE.md`

1. 코드 패치 적용
2. `agents/lessons_learned.md` 교훈 수동 기록 (중복·단순 에러 로그는 생략)
3. 재실행으로 통과 확인
