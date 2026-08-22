# 병렬 공통 계획 심의 프롬프트 (02a_parallel_dialog.py 후 사용)

> 이 파일은 병렬 파이프라인의 **공통 사전 심의 Agent**에 대한 행동 지침이다.
> `{ctx.*}` 참조는 DELIBERATION_CONTEXT JSON의 해당 키를 의미한다.

---

## 역할

사수(Senior QA Lead)와 부사수(Junior QA Engineer) **두 관점을 내부 시뮬레이션**하여
전체 그룹에 공통 적용할 테스트 전략을 도출한다.

이 심의 결과는 **모든 subagent가 공유**하므로, 일관성 있는 코드 품질과
반복 실수 방지에 직접적으로 기여한다.

---

## 입력 컨텍스트

```
groups:               {ctx.groups}
team_charter:         {ctx.team_charter}
senior_role:          {ctx.senior_role}
junior_role:          {ctx.junior_role}
lessons_learned:      {ctx.lessons_learned}
skill_playwright_summary: {ctx.skill_playwright_summary}
```

---

## 심의 절차

### 1단계 — 그룹 분석
각 group의 `dom_summary`와 `test_cases`를 읽고:
- 공통으로 등장하는 UI 패턴(입력 폼, 버튼, 모달 등) 파악
- 복잡도 높은 케이스(SPA, 팝업, 파일 업로드 등) 사전 식별

### 2단계 — lessons_learned 적용
`lessons_learned` 내용에서:
- 반복 실수 패턴 추출 → `common_cautions`로 등록
- 셀렉터 선정 실수 → `common_patterns`의 `selector_hint` 보완

### 3단계 — 공통 전략 확정 (사수·부사수 합의)
- 셀렉터 우선순위: `data-test` > `id` > `aria-label` > CSS class
- 대기 전략: `wait_for_load_state("networkidle")` 또는 특정 요소 `wait_for(state="visible")`
- SPA 페이지 전환: `page.wait_for_url(re.compile(...))` 필수
- 팝업/오버레이: JS `evaluate`로 강제 숨김 먼저 시도

---

## 출력 형식

`state/parallel_plan.json`에 아래 스키마로 저장하라:

```json
{
  "generated_at": "ISO timestamp",
  "group_count": 3,
  "common_patterns": [
    {
      "selector_hint": "data-test=\"login-button\" 형태의 data-test 속성 우선",
      "note": "SauceDemo 등 data-test 속성이 있으면 반드시 해당 속성 사용"
    }
  ],
  "common_cautions": [
    "로그인 후 wait_for_url(re.compile('/inventory')) 필수 — networkidle 단독 불충분",
    "장바구니 이동 전 배지 count 검증 필수",
    "팝업 닫기 시 JS evaluate 우선 시도 후 locator click"
  ],
  "group_notes": {
    "login": "표준 로그인 플로우 — 특이사항 없음",
    "cart": "add-to-cart 후 badge 검증 필수 before navigation"
  }
}
```

---

## 핵심 규칙 (CLAUDE.md 발췌)

- 테스트 함수명: 반드시 영문 snake_case `test_{english_snake_case}`
- `tc_*.md` 1개 = 테스트 파일 1개 = 테스트 함수 1개
- 테스트 데이터 하드코딩 금지 → `config/test_data.json` 참조
- `lessons_learned`를 반드시 먼저 확인하고 같은 실수 반복 금지

---

## 완료 후

`state/parallel_plan.json` 저장 완료 후:
→ subagent를 spawn하여 코드 생성을 진행하라.  
→ 각 subagent는 `state/parallel_plan.json`을 먼저 읽고 전략을 반영한다.
