# 힐링 가이드

> **독자**: Claude Code — 힐링 루프 진입 시 읽음 (`06_heal.py` 또는 `99_merge.py` 실패 후).
> MCP 시각 검증 절차, 힐링 완료 체크리스트, 배치 병렬화 기준을 확인할 때 참조.
> 스킬: [Heal Patterns](.claude/skills/heal-patterns/SKILL.md) (오류 유형별 패치 전략)

모든 파이프라인(단일/병렬)에서 힐링 시 동일 기준 적용.
단일(`06_heal.py` + `06_auto_heal.py`)과 병렬(`99_merge.py`)이 동일한 힐링 플로우를 공유:
에러 분류(7종) → 사이트 사전 접근 체크 → 반복 실패 감지(2회 스킵) → auto_heal(deterministic 패치) → **배치 분할 병렬 힐링**(HEAL_SUBAGENT_CONTEXTS, 배치당 6건) → lessons/heal_stats 기록.

> 오류 유형별 패치 전략 상세: `.claude/skills/heal-patterns/SKILL.md`
> Playwright 코드 작성 베스트프랙티스: `.claude/skills/playwright-best-practices/SKILL.md`

## [필수] 힐링 완료 체크리스트

하나라도 빠지면 힐링 미완료:

1. 코드 패치 적용
2. `agents/lessons_learned.md`에 교훈을 수동 기록 (자동 로그는 `heal_utils.py`가 `lessons_learned_auto.md`에 기록):
   ```
   - **{핵심 키워드}**: {상황 설명}. {해결법/교훈}
   ```
3. 재실행으로 통과 확인

## 힐링 제한 및 재실행 옵션

**최대 3회 제한**: 06_heal.py만 `heal_count`를 증가시킴 (05_execute.py는 읽기만 함). 초과 시 `step = "heal_failed"`, 종료코드 2로 중단.

**종료코드:**
| 코드 | 의미 |
|------|------|
| 0 | 실패 없음 (힐링 불필요) |
| 10 | 실패 정보 저장 완료, Claude Code 패치 필요 |
| 2 | 최대 힐링 횟수(3회) 초과 — 파이프라인 중단 |

**--only-failed 옵션**: 이전 실행 결과의 실패 테스트만 선택적으로 재실행
```bash
python scripts/05_execute.py --only-failed [--no-report]
```
- 성공한 테스트는 건너뜀
- 힐링 중간 재실행 속도 향상 (불필요한 테스트 제외)
- 전체 통과 후 최종 실행 시에는 전체 재실행 권장

## 빈도 데이터 활용

- `06_heal.py`가 실패 시 `state/heal_stats.json`에 오류 패턴별 빈도 자동 기록
- `06a_dialog.py`가 Top 5 빈출 패턴을 DELIBERATION_CONTEXT에 자동 주입
- 빈출 패턴은 힐링 시 우선 점검 대상

## OMC ultraqa를 이용한 자동 힐링

손수 패치하는 대신 `/oh-my-claudecode:ultraqa` 스킬로 자동 힐링 가능:

```
python scripts/05_execute.py --no-report
(실패 발생 시)
/oh-my-claudecode:ultraqa
  - 목표: 실패 테스트 자동 분석 후 패치 + 재실행
  - 최대 3회까지 자동 반복 (초과 시 중단)
  - 명령: .venv/bin/python -m pytest tests/generated/{group}/ -n 8 --tb=short
```

**주의**: ultraqa는 최대 3회 제한을 추적하므로, 3회 초과 실패는 수동 개입 필요.

## MCP 시각 검증

`heal_context.mcp_snapshot_recommended`가 `true`이면 해당 배치의 heal agent가 자동으로 실시간 DOM을 확인한다 (Locator/Assertion/Timeout 오류 시 `06_heal.py`가 자동 설정).
traceback만으로 원인이 불명확한 경우에도 수동으로 사용할 수 있다.

MCP 호출 실패 시 dom_info 기반 힐링으로 자동 전환 (graceful degradation).

1. **스크린샷 확인**: Read tool로 `heal_context.failures[].screenshot.path` 파일 열기 → 실패 시점 화면 확인
2. **Trace 확인** (네트워크·콘솔 오류 의심 시): `meta.json`의 `trace_path` 참조 → `npx playwright show-trace <파일>.zip` (영상·네트워크·콘솔·DOM 스냅샷 포함)
3. **실제 페이지 탐색** (필요 시만):
   - `browser_navigate` → heal_context의 URL로 접속
   - `browser_snapshot` → 현재 페이지 ARIA 트리 + DOM 구조 확인
3. **셀렉터 검증** (필요 시만):
   - `browser_evaluate` → `document.querySelector('셀렉터')` 로 셀렉터 존재 확인
4. **패치 적용**: 시각 검증 결과를 바탕으로 테스트 코드 수정

**주의사항**:
- MCP 브라우저와 pytest 브라우저는 별개 세션이므로 쿠키/상태가 공유되지 않는다
- 로그인 등 전제조건이 필요한 페이지는 DOM/텍스트 확인에 그친다
