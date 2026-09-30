# 프롬프트 템플릿 레퍼런스

> **문서 유형: 프롬프트 레퍼런스** · 컨텍스트 입력과 프롬프트 템플릿 참고. 최신 구현은 해당 스크립트와 prompts/ 파일을 기준으로 확인합니다.

> **독자**: 사람 — `prompts/` 폴더 내 템플릿의 입출력 스키마 정의.

---

## 프롬프트 파일 목록

| 파일 | 생성 스크립트 | 파이프라인 단계 | 출력 대상 |
|------|-------------|----------------|----------|
| `plan_deliberation.md` | `02a_dialog.py` | 2단계: Plan 심의 | `state/pipeline.json` plan |
| `review_deliberation.md` | `03a_dialog.py` | 5단계: 코드 리뷰 심의 | `state/pipeline.json` review_summary |
| `heal_deliberation.md` | `06a_dialog.py` | 8단계: 힐링 심의 | 코드 패치 파일 직접 수정 |
| `parallel_subagent.md` | `run_qa_parallel.py` | 병렬 파이프라인 각 Subagent | `tests/generated/{group}/tc_*.py` |
| `team_discussion.md` | `scripts/team_discuss.py` | 팀 토론 멀티라운드 | `agents/dialog.json` |

---

## DELIBERATION_CONTEXT 주입 변수

`*a_dialog.py`가 파일을 병렬 읽기 후 JSON으로 출력. Claude가 이 JSON을 프롬프트에 직접 포함. P64 이후 Plan·코드 리뷰는 페르소나 없이 체크리스트로 수행하며, 사수/부사수 관점은 힐링·팀 토론에 사용합니다.

### `02a_dialog.py` → `plan_deliberation.md`

```json
{
  "dom_info": { "inputs": [], "buttons": [], "components": [], ... },
  "test_cases": [{ "id": "tc_01", "title": "...", "steps": [] }],
  "lessons_learned": "(agents/lessons_learned.md 전체 텍스트)"
}
```

### `03a_dialog.py` → `review_deliberation.md`

```json
{
  "lint_result": { "issues": [], "pass": true },
  "plan": [{ "id": "tc_01", "file": "tc_01_login.py", "strategy": "..." }],
  "generated_files": ["tc_01_login.py", ...],
  "lessons_learned": "(agents/lessons_learned.md 전체 텍스트)"
}
```

### `06a_dialog.py` → `heal_deliberation.md`

```json
{
  "dom_info": { ... },
  "failures": [
    { "test_id": "", "test_name": "", "traceback": "", "error_type": "Locator", "screenshot": null }
  ],
  "failure_groups": { "Locator": ["test_a"], "Assertion": ["test_b"] },
  "heal_stats_top5": [
    { "key": "Locator::...", "count": 5, "error_type": "Locator", "summary": "..." }
  ],
  "lessons_learned": "(agents/lessons_learned.md 전체 텍스트)",
  "lessons_auto": "(agents/lessons_learned_auto.md 전체 텍스트)"
}
```

---

## `prompts/examples/` — Few-shot 예시

| 파일 | 용도 | 참조 위치 |
|------|------|----------|
| `plan_good.json` | 올바른 plan 구조 예시 | `plan_deliberation.md` 내부 참조 |
| `plan_bad.json` | 흔한 plan 실수 예시 | `plan_deliberation.md` 내부 참조 |
| `heal_patch.json` | 오류 유형별 before/after 패치 예시 | `heal_deliberation.md` 내부 참조 |
