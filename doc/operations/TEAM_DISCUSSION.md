# 팀 자유 토론 파이프라인

> **문서 유형: 에이전트 운영 지침** · 대시보드 팀 토론 기능의 저장·승인 절차. 승인에 따른 자동 구현 동작을 포함합니다.

> **독자**: Claude Code — 사용자가 팀 토론을 요청할 때 읽음 (`run_team.py` 실행 후 또는 대시보드 토론 시작 시).
> QA 파이프라인 심의(Plan·코드리뷰·힐링)와 무관. 팀 토론 전용 플로우.

사용자가 `run_team.py`를 실행하면 아래 순서로 진행한다.
어떤 주제든 사수/부사수가 토론하고, 사용자가 결론을 최종 승인한다.

## 실행 순서

```
.venv/bin/python run_team.py --topic "주제"
  → state/discuss.json 초기화
```

**1.** `.venv/bin/python scripts/team_discuss.py` 실행
   출력에서 `DELIBERATION_CONTEXT_START ~ END` 사이의 JSON 추출.
   **[심의 Agent — 멀티라운드 티키타카 진행]** — `prompts/team_discussion.md` 템플릿 참조.
   DELIBERATION_CONTEXT JSON의 각 필드를 템플릿의 `{ctx.*}` 자리에 대입해 agent 실행.

   > **핵심 규칙: 발언 1개 작성 → 즉시 dialog.json 저장 → 다음 발언 작성 → 즉시 저장 → 반복**
   > 배치 저장 금지. 대시보드가 3초마다 폴링하므로 한 발언씩 저장해야 실시간으로 보인다.

   결론 저장:
   state/discuss.json → `{ "step": "discussed", "conclusion": "결론 (마크다운)" }`

**2.** 심의 완료 후 사용자에게 알림:
   "토론이 완료됐어요. 대시보드에서 결론을 확인하고 승인/반려해주세요."
   (대시보드 http://localhost:8766 → 해당 토론 세션 하단에 승인/반려 버튼이 표시됩니다)
   - 승인 시: 서버가 `agents/team_notes.md` 저장 + `pending_impl.json` 생성
     → 스케줄러(2분 내)가 `pending_impl.json` 감지 → Claude가 항목 자동 구현
     → 구현 완료 후 `pending_impl.json` 삭제, `team_notes.md`·`state/discuss.json` 초기화
   - 반려 시: rejection_reason 저장, state/discuss.json step = "rejected" → 재토론 요청
