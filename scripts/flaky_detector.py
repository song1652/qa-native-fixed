"""
Flaky Test 감지기
run_history.json의 per_test_results 필드를 분석하여
여러 실행에서 Pass/Fail이 반복되는 테스트를 감지하고
state/flaky_tests.json에 저장한다.
"""
import json
from datetime import datetime
from pathlib import Path

from _paths import PROJECT_ROOT, RUN_HISTORY as RUN_HISTORY_PATH, FLAKY_TESTS_PATH


def detect_flaky(
    run_history: list,
    min_runs: int = 3,
    flaky_lo: float = 0.2,
    flaky_hi: float = 0.8,
) -> list:
    """
    per_test_results 기반으로 flaky 테스트 목록 반환.
    pass_rate가 flaky_lo ~ flaky_hi 구간에 있는 테스트 = flaky.
    """
    test_records: dict[str, list[str]] = {}  # {test_id: ["pass", "fail", ...]}

    for run in run_history:
        per = run.get("per_test_results")
        if not per:
            continue
        for test_id, result in per.items():
            if test_id not in test_records:
                test_records[test_id] = []
            test_records[test_id].append(result)

    flaky = []
    for test_id, results in test_records.items():
        if len(results) < min_runs:
            continue
        recent = results[-10:]  # 최근 10회만 분석
        pass_count = sum(1 for r in recent if r == "pass")
        pass_rate = pass_count / len(recent)
        if flaky_lo <= pass_rate <= flaky_hi:
            flaky.append({
                "test_id": test_id,
                "pass_rate": round(pass_rate, 2),
                "runs": len(recent),
                "recent": recent[-5:],  # 최근 5회 도트용
            })

    return sorted(flaky, key=lambda x: x["pass_rate"])


def main():
    if not RUN_HISTORY_PATH.exists():
        print("[flaky_detector] run_history.json 없음")
        return

    history = json.loads(RUN_HISTORY_PATH.read_text(encoding="utf-8"))
    flaky = detect_flaky(history)

    result = {
        "flaky": flaky,
        "checked_at": datetime.now().isoformat(),
        "total_runs_analyzed": len(history),
    }
    FLAKY_TESTS_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if flaky:
        print(f"[flaky_detector] Flaky 테스트 {len(flaky)}건 감지:")
        for f in flaky:
            print(f"  {f['test_id']}  pass_rate={f['pass_rate']:.0%}  최근={f['recent']}")
    else:
        print("[flaky_detector] Flaky 테스트 없음")


if __name__ == "__main__":
    main()
