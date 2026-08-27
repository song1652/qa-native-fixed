"""
Step 4 -- QA 리드 승인 게이트
LLM 없음. state.json의 review_summary를 출력하고 y/n 입력 대기.
결과를 state.json의 approval_status에 저장.

종료코드: 0=승인  4=반려(재작성)  1=stdin 없음(비대화형 환경, 승인 UI 없음)  2=3회 반려 초과
step은 변경하지 않음 (reviewed 유지) — 05_execute.py가 done/heal_needed로 전이.
auto_approve: config/pipeline.json의 auto_approve=true 또는 --yes 플래그로 활성화.

비대화형(headless) 환경에서는 반드시 auto_approve 또는 --yes를 써야 한다.
예전엔 stdin이 없으면 "대시보드 대기"(exit 3)로 빠졌는데, 대시보드엔 이
승인/반려 UI가 실제로 없어(#26) 켜두면 파이프라인이 영구 정지하는
데드엔드였다. 그 폴백은 제거했다 — check_pending_approve.py도 이미
"승인 단계 제거 -- 심의 완료 후 바로 실행"으로 문서화돼 있어 실제 훅
주도 흐름은 이 게이트를 기다리지 않는다.
"""
import argparse
import json
import sys
from pathlib import Path
from _paths import PIPELINE_STATE, read_state, update_state
from _constants import EXIT_REJECTED, EXIT_HEAL_EXCEEDED

MAX_REJECTION = 3  # 반려 최대 횟수 — 초과 시 파이프라인 강제 종료

# 주의: config/pipeline.json (동작 설정, 이 파일)과 state/pipeline.json (런타임 상태, PIPELINE_STATE)은
# 파일명만 같을 뿐 서로 다른 파일이다. 혼동 주의.
_PIPELINE_CONFIG = Path(__file__).parent.parent / "config" / "pipeline.json"


def _parse_args():
    parser = argparse.ArgumentParser(description="Step 4: QA 리드 승인 게이트")
    parser.add_argument("--yes", action="store_true",
                        help="자동 승인 (CI/headless 환경)")
    return parser.parse_args()


def _auto_approve_enabled(yes_flag: bool) -> bool:
    if yes_flag:
        return True
    try:
        cfg = json.loads(_PIPELINE_CONFIG.read_text(encoding="utf-8"))
        return bool(cfg.get("auto_approve", False))
    except Exception:
        return False


def main():
    args = _parse_args()
    state_path = PIPELINE_STATE
    if not state_path.exists():
        print("[오류] state/pipeline.json 없음.")
        sys.exit(1)

    state = read_state(state_path)

    print()
    print("=" * 60)
    print("  QA 리드 승인 요청")
    print("=" * 60)
    print(f"  URL   : {state['url']}")
    print(f"  케이스 : {len(state['test_cases'])}개")
    print()

    summary = state.get("review_summary", "요약 없음")
    print("[ 리뷰 요약 ]")
    print(summary)
    print()

    lint = state.get("lint_result", {})
    lint_status = "통과" if lint.get("passed") else f"이슈 {lint.get('issue_count', '?')}건"
    print(f"[ lint ] {lint_status}")
    print()

    file_path = state.get("generated_file_path", "")
    print(f"[ 코드 ] {file_path}")
    print()
    print("=" * 60)

    # config/pipeline.json auto_approve=true 또는 --yes → 즉시 승인
    if _auto_approve_enabled(args.yes):
        update_state(state_path, lambda s: {**s, "approval_status": "approved"})  # P43
        print("  [자동 승인] config/pipeline.json auto_approve=true")
        return

    # CLI 모드: stdin 입력 대기
    try:
        while True:
            answer = input("  승인하시겠습니까? (y=승인 / n=반려): ").strip().lower()
            if answer in ("y", "yes", "n", "no"):
                break
            print("  y 또는 n을 입력하세요.")
    except EOFError:
        # state는 건드리지 않는다 -- approval_status="pending"을 썼다간 아무도
        # 소비하지 않는 채로 파이프라인이 조용히 멈춘 것처럼 보인다 (#26).
        print()
        print("  [오류] stdin이 없어 승인 입력을 받을 수 없습니다.")
        print("  이 파이프라인엔 승인 대기 UI가 없습니다.")
        print("  config/pipeline.json의 auto_approve=true 또는 --yes 플래그를 사용하세요.")
        sys.exit(1)

    approved = answer in ("y", "yes")

    if approved:
        update_state(state_path, lambda s: {**s, "approval_status": "approved"})  # P43
        print()
        print("  [승인] 테스트를 실행합니다.")
    else:
        try:
            reason = input("  반려 사유를 입력하세요: ").strip()
        except EOFError:
            reason = ""
        _rejection_reason = reason or "사유 미입력"
        # rejection_count 증가를 mutator 내부에서 수행 → 원자적 RMW (P43)
        updated = update_state(state_path, lambda s: {
            **s,
            "approval_status": "rejected",
            "rejection_reason": _rejection_reason,
            "rejection_count": s.get("rejection_count", 0) + 1,
        })
        print()
        print(f"  [반려] 사유: {_rejection_reason}")
        rejection_count = updated["rejection_count"]
        print(f"  반려 횟수: {rejection_count}회")
        if rejection_count >= MAX_REJECTION:
            print(f"  [경고] {MAX_REJECTION}회 반려 한도 초과. 파이프라인을 종료합니다.")
            print("  수동으로 코드를 검토하거나 테스트케이스를 수정하세요.")
            sys.exit(EXIT_HEAL_EXCEEDED)
        print()
        print("[다음] Claude Code가 반려 사유를 반영해 코드를 재작성합니다.")
        sys.exit(EXIT_REJECTED)


if __name__ == "__main__":
    main()
