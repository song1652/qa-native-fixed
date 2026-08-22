"""
병렬 파이프라인 공통 사전 심의 컨텍스트 준비 (02a_parallel_dialog.py)
LLM 없음. state/parallel_contexts.json을 읽어 전체 그룹의 공통 테스트 전략 수립을
위한 심의 컨텍스트를 출력한다.

실행 시점: run_qa_parallel.py 이후, subagent spawn 이전
출력: DELIBERATION_CONTEXT_START ~ END (JSON)

심의 후: Claude가 state/parallel_plan.json에 공통 전략을 저장해야 한다.
그러면 subagent들이 shared_context_paths.parallel_plan 경로로 읽어 참조한다.

저장 형식:
{
  "common_patterns":  [{"selector": "...", "note": "..."}],
  "common_cautions":  ["SPA 이벤트 처리 필요", "팝업 닫기 필수 등"],
  "group_notes":      {"group_dir": "그룹별 특이사항"}
}
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

CONTEXTS_PATH = PROJECT_ROOT / "state" / "parallel_contexts.json"
PLAN_PATH = PROJECT_ROOT / "state" / "parallel_plan.json"

# 공통 참조 파일 경로
_SHARED_PATHS = {
    "team_charter":       PROJECT_ROOT / "agents/team_charter.md",
    "senior_role":        PROJECT_ROOT / "agents/roles/senior.md",
    "junior_role":        PROJECT_ROOT / "agents/roles/junior.md",
    "lessons_learned":    PROJECT_ROOT / "agents/lessons_learned.md",
    "skill_playwright":   PROJECT_ROOT / ".claude/skills/playwright-best-practices/SKILL.md",
    "plan_deliberation":  PROJECT_ROOT / "prompts/plan_deliberation.md",
}

# DOM 필드 경량화: 토큰 절약을 위해 상위 N개만 포함
_DOM_SUMMARY_LIMIT = 10


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _summarize_dom(dom_info: dict) -> dict:
    """DOM 정보를 경량화 (전체 전달 시 토큰 폭발 방지)."""
    return {
        "title":      dom_info.get("title", ""),
        "inputs":     dom_info.get("inputs", [])[:_DOM_SUMMARY_LIMIT],
        "buttons":    dom_info.get("buttons", [])[:_DOM_SUMMARY_LIMIT],
        "components": dom_info.get("components", [])[:5],
        "forms_count": dom_info.get("forms_count", 0),
    }


def main() -> None:
    if not CONTEXTS_PATH.exists():
        print("[오류] state/parallel_contexts.json 없음. run_qa_parallel.py를 먼저 실행하세요.")
        sys.exit(1)

    payload = json.loads(CONTEXTS_PATH.read_text(encoding="utf-8"))
    subagents = payload.get("subagents", [])

    if not subagents:
        print("[오류] subagents 목록이 비어있습니다.")
        sys.exit(1)

    # 공통 참조 파일 병렬 읽기
    with ThreadPoolExecutor() as ex:
        futures = {k: ex.submit(_read_file, v) for k, v in _SHARED_PATHS.items()}
        ctx = {k: f.result() for k, f in futures.items()}

    # 그룹별 요약 (dom_info 경량화)
    group_summaries = []
    url_seen: set[str] = set()
    for ag in subagents:
        group_summaries.append({
            "group_dir":  ag["group_dir"],
            "group_label": ag.get("group_label", ag["group_dir"]),
            "url":        ag["url"],
            "test_cases": ag["test_cases"],
            "dom_summary": _summarize_dom(ag.get("dom_info", {})),
            "batch_info": ag.get("batch_info", ""),
            "test_data":  ag.get("test_data", {}),
        })
        url_seen.add(ag["url"])

    total_cases = sum(len(ag["test_cases"]) for ag in subagents)

    context_payload = {
        "stage": "parallel_planning",
        "group_count": len(subagents),
        "unique_url_count": len(url_seen),
        "total_cases": total_cases,
        "groups": group_summaries,
        "team_charter": ctx["team_charter"],
        "senior_role": ctx["senior_role"],
        "junior_role": ctx["junior_role"],
        "lessons_learned": ctx["lessons_learned"],
        "skill_playwright_summary": ctx["skill_playwright"][:3000],  # 처음 3000자만 (전략 힌트)
        "plan_deliberation_guide": ctx["plan_deliberation"],
        "output_path": str(PLAN_PATH),
        "instruction": (
            "위 groups 배열의 모든 그룹을 분석해 공통 테스트 전략을 수립하라.\n"
            "사수(Senior QA Lead)와 부사수(Junior QA Engineer) 두 관점을 내부 시뮬레이션하여 결론을 도출.\n\n"
            "분석 항목:\n"
            "1. 공통 셀렉터 패턴: 여러 그룹에서 공통으로 나타나는 UI 패턴 및 안전한 셀렉터 전략\n"
            "2. 공통 주의사항: SPA 이벤트, 팝업/오버레이, 로그인 순서, 네트워크 대기 등\n"
            "3. 그룹별 특이사항: 각 group_dir의 DOM 특성·예외 케이스\n"
            "4. lessons_learned에서 반복 실수 패턴 추출 → 공통 caution으로 등록\n\n"
            f"결과를 {PLAN_PATH} 에 아래 JSON 스키마로 저장하라:\n"
            "{\n"
            '  "common_patterns": [{"selector_hint": "...", "note": "..."}],\n'
            '  "common_cautions": ["주의사항1", "주의사항2"],\n'
            '  "group_notes": {"group_dir": "그룹 특이사항 (없으면 생략)"}\n'
            "}"
        ),
    }

    print("[02a-parallel] 병렬 공통 심의 컨텍스트 준비 완료")
    print(f"  그룹 수: {len(subagents)}개  /  고유 URL: {len(url_seen)}개  /  총 케이스: {total_cases}개")
    print(f"  심의 결과 저장 위치: {PLAN_PATH}")
    print()
    print("=== DELIBERATION_CONTEXT_START ===")
    print(json.dumps(context_payload, ensure_ascii=False))
    print("=== DELIBERATION_CONTEXT_END ===")
    print()
    print("─" * 60)
    print("  [심의 Agent 지시]")
    print("  위 DELIBERATION_CONTEXT를 바탕으로 공통 테스트 전략을 수립하고")
    print(f"  결과를 {PLAN_PATH} 에 JSON으로 저장하라.")
    print("  저장 완료 후: subagent를 spawn하여 코드 생성을 진행하라.")
    print("─" * 60)


if __name__ == "__main__":
    main()
