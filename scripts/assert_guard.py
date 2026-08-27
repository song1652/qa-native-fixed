"""
Step 6b -- Assert Guard: 힐링 패치 후 assertion 약화 감지

06_heal.py가 original_assertions(최초 기준)와 pre_heal_assertions를 저장한 뒤,
Agent가 코드를 패치한 다음 이 스크립트를 실행한다.

패치 전후 assertion을 비교해 약화 패턴을 감지하고
state/pipeline.json의 assertion_integrity 필드에 저장.
06a_dialog.py가 이 결과를 심의 컨텍스트에 자동 주입한다.

비교 기준:
  original_assertions (최초 생성 시점, 고정) — 누적 약화 감지
  pre_heal_assertions (직전 패치 기준) — fallback

종료 코드:
  0 = 정상 (약화 없음 또는 경고만 기록)
  1 = 기준 스냅샷 없음 (06_heal.py 먼저 실행 필요)
"""
import sys
from pathlib import Path

from _paths import PIPELINE_STATE, read_state, update_state
from _constants import DEFAULT_GENERATED_DIR
from heal_utils import snapshot_assertions, compare_assertions


def main():
    state_path = PIPELINE_STATE
    if not state_path.exists():
        print("[assert_guard] state/pipeline.json 없음.")
        sys.exit(1)

    state = read_state(state_path)

    # original_assertions: 최초 생성 시점 고정 기준 (누적 약화 감지)
    # pre_heal_assertions: 직전 패치 기준 (fallback)
    baseline = state.get("original_assertions") or state.get("pre_heal_assertions")

    if not baseline:
        print("[assert_guard] original_assertions 없음 — 06_heal.py를 먼저 실행하세요.")
        sys.exit(1)

    is_cumulative = bool(state.get("original_assertions"))
    baseline_label = "최초 생성 기준" if is_cumulative else "직전 패치 기준"

    # 패치 후 현재 파일 스냅샷
    generated_path = Path(state.get("generated_file_path", DEFAULT_GENERATED_DIR))
    file_paths: list[str] = []
    for fname in baseline:
        if generated_path.is_dir():
            file_paths.append(str(generated_path / fname))
        else:
            file_paths.append(str(generated_path.parent / fname))

    post_snap = snapshot_assertions(file_paths)
    result = compare_assertions(baseline, post_snap)
    result["baseline"] = baseline_label
    result["heal_round"] = state.get("heal_count", 1)

    # P69: update_state 원자적 RMW — read→파싱→write 사이 다른 프로세스 갱신 유실 방지
    update_state(state_path, lambda fresh: {**fresh, "assertion_integrity": result})

    if result["has_warnings"]:
        print(f"[assert_guard] ⚠️  assertion 약화 패턴 감지 ({baseline_label}, {result['heal_round']}회차):")
        for w in result["warnings"]:
            print(f"  - {w}")
        print()
        print("  → 06a_dialog.py 심의 컨텍스트에 포함됩니다.")
        print("  → 04_approve 승인 시 반드시 확인하세요.")
    else:
        print(f"[assert_guard] assertion 품질 이상 없음 ({baseline_label}).")

    sys.exit(0)


if __name__ == "__main__":
    main()
