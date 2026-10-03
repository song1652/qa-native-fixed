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
  "failure_groups": { "Locator": ["test_a"] },
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

## 안전 복구와 실행 중단 (2026-10-03)

- 프롬프트 실행 전에 실행 결과의 모든 단계 오류와 종료 코드를 분류합니다. 요소 오류만 복구 컨텍스트를 생성하며, 기대값 불일치·환경·전송·세션·설정 오류와 비정상 종료는 사용자 확인 대상으로 둡니다.
- 복구 컨텍스트의 `fresh_dom_info`는 해당 실행의 현재 URL에서 새로 수집한 화면입니다. 누락·수집 실패 시 과거 DOM으로 대체하지 않습니다.
- 코드 수정 검증 실패 시 원본을 복원하고 `recovery_stopped`를 기록합니다. 자동 복구 종료 코드 **5**는 추가 Agent 호출이나 테스트 재실행을 중단하라는 계약입니다.
- `workflow_status`가 `failed`, `cancelled`, `interrupted`, `timed_out`, `incomplete`이면 프롬프트 훅이 이전 단계·복구 컨텍스트를 재주입하지 않습니다. 서버 재시작 후에도 단계를 자동 재개하지 않습니다.
- 전체 운영 절차는 [힐링 지침](../operations/HEALING_GUIDE.md), 실행별 상태 계약은 [파이프라인 상태](PIPELINE_STATE.md)를 참고하세요.
