# Lessons Learned (Auto) — 자동 기록 힐링 패턴

> **독자**: 심의 Agent — 힐링 시 보조 참조. 큐레이션 패턴([lessons_learned.md](lessons_learned.md)) 우선 확인 후 이 파일로 최신 패턴 보완.
> **읽는 시점**: `06a_dialog.py`가 DELIBERATION_CONTEXT에 lessons_snapshot으로 자동 주입하므로, Agent가 직접 읽을 필요는 드뭄. 최신 자동 기록 직접 확인 시에만 Read.
> **자동 생성 파일**: `heal_utils.py`의 `append_lessons()`가 힐링 시 자동 기록. 수동 편집 금지.

---
## Timeout 오류

- **Timeout**: `TimeoutError: site unreachable` -- expect(..., timeout=10000) 또는 wait_for_selector 추가

- **Timeout**: `tests/generated/login/tc_99_heal_test.py:15: in test_heal_timeout_example` -- expect(..., timeout=10000) 또는 wait_for_selector 추가
