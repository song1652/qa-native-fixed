"""
병렬 파이프라인 Step 99 - 실행 + 통합 리포트 (P84: 모듈 분리 리팩토링)

1. tests/generated/ 에서 pytest 일괄 실행 (JSON 리포트)
2. 실패 시 heal_context 저장 → Claude Code 힐링 루프 (최대 3회)
3. 그룹별 PASS/FAIL 집계
4. HTML 리포트 생성 (tests/reports/parallel_index_{ts}.html)

LLM 없음. 순수 Python.
세부 로직은 모듈로 분리:
  _exec.py    — 파일 수집 + pytest 실행
  _healer.py  — 힐링 판단·실행
  _report.py  — HTML 리포트 생성
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from _paths import (
    PROJECT_ROOT, PARALLEL_STATE, HEAL_CONTEXT_STATE, QUICK_STATE,
    read_state, update_state, append_run_history,
)
from _constants import MAX_HEAL
from _pipeline_registry import ParallelStatus
from result_parser import parse_results, parse_skip_messages
from structured_log import slog

# 분리된 모듈
from _exec   import collect_test_files, run_pytest, is_spa_group
from _healer import (
    should_heal, run_heal_cycle,
    verify_lessons_learned_updated,
    check_assertion_integrity,
)
from _report import build_parallel_html

GENERATED_DIR  = PROJECT_ROOT / "tests" / "generated"
SCREENSHOTS_DIR = PROJECT_ROOT / "tests" / "screenshots"


# ── 상태 업데이트 헬퍼 ───────────────────────────────────────────────────────


def _update_parallel_status(
    status: str,
    extra: dict | None = None,
    *,
    path: Path | None = None,
) -> None:
    """state/parallel.json(또는 path)의 status 필드를 업데이트 (원자적 RMW).

    Args:
        status: 설정할 새 status 값.
        extra:  추가로 병합할 필드 딕셔너리.
        path:   상태 파일 경로. None이면 PARALLEL_STATE.
                quick 모드에서는 QUICK_STATE를 전달한다 (P41).
    """
    def _mutator(fresh: dict) -> dict:
        updated = {**fresh, "status": status}
        if extra:
            updated.update(extra)
        return updated
    update_state(path or PARALLEL_STATE, _mutator)


# ── 메인 ─────────────────────────────────────────────────────────────────────


def main() -> None:
    import argparse
    import time as _time

    parser = argparse.ArgumentParser(description="QA 테스트 실행 + 리포트 생성")
    parser.add_argument(
        "--group", "-g", nargs="*", metavar="FOLDER",
        help="실행할 폴더명 (예: login checkout). 생략 시 전체 실행.",
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="빠른 실행 모드: state/quick.json에 결과 저장 (parallel_state 미변경)",
    )
    parser.add_argument(
        "--no-heal", action="store_true",
        help="힐링 단계 생략: 실패해도 heal_context를 생성하지 않음",
    )
    args = parser.parse_args()

    _start_time = _time.monotonic()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")

    quick_mode = args.quick
    state_path = QUICK_STATE if quick_mode else PARALLEL_STATE

    # ── (A) 파일 수집 ──────────────────────────────────────────────
    sorted_files, scope_label = collect_test_files(args.group)
    if not sorted_files:
        return

    slog("step_start", step="99_merge", scope=scope_label,
         file_count=len(sorted_files), quick=quick_mode)
    print(f"\n[99] 실행 범위: {scope_label}  ({len(sorted_files)}개 케이스, 순차 실행)")

    # 스크린샷 정리 (최종 실패 시만 남기기)
    if SCREENSHOTS_DIR.exists():
        shutil.rmtree(SCREENSHOTS_DIR, ignore_errors=True)

    # M-4: TERMINAL 상태에서 새 실행 시작 시 heal_count 리셋.
    # HEAL_NEEDED(힐링 재실행) 상태이면 리셋하지 않아 누적 카운트를 유지.
    _pre_run_state = read_state(state_path)
    _prev_run_status = (_pre_run_state or {}).get("status", "")
    _TERMINAL_STATUSES = {
        ParallelStatus.DONE, ParallelStatus.HEAL_FAILED,
        ParallelStatus.ERROR, ParallelStatus.INIT, ParallelStatus.EMPTY,
    }
    if _prev_run_status in _TERMINAL_STATUSES:
        update_state(state_path, lambda fresh: {**fresh, "heal_count": 0})

    # FSM: TESTING으로 전이 (P41 — done→testing→결과 경로 확보)
    _update_parallel_status(ParallelStatus.TESTING, path=state_path)

    # 이전 heal_count 읽기 (병렬 상태 파일에서, 단일 파이프라인 오염 방지)
    _prev_state = read_state(state_path)
    heal_count = _prev_state.get("heal_count", 0)

    # 힐링 재실행 시 lessons_learned 기록 검증
    _prev_ctx = read_state(HEAL_CONTEXT_STATE)
    heal_analyzed_at = _prev_ctx.get("analyzed_at") if _prev_ctx else None
    if heal_count > 0 and heal_analyzed_at:
        verify_lessons_learned_updated(heal_analyzed_at)

    # ── (B) pytest 실행 ────────────────────────────────────────────
    # spa: true 그룹은 세션 충돌 방지를 위해 단일세션(순차) 실행
    _single_session = is_spa_group(args.group)
    if _single_session:
        print(f"[99] SPA 사이트 감지 → 단일세션 순차 실행")
    pytest_exit_code, report = run_pytest(sorted_files, single_session=_single_session)
    test_results    = parse_results(report)
    pytest_summary  = report.get("summary", {})
    failed_count    = pytest_summary.get("failed", 0) + pytest_summary.get("error", 0)

    # P73: pytest exit 5 = 수집된 테스트 없음
    if pytest_exit_code == 5 and failed_count == 0:
        print("\n[99] ⚠️ pytest 종료코드 5 — 수집된 테스트 없음")
        print("     tests/generated/ 디렉토리가 비어있거나 tc_*.py 파일이 없습니다.")
        print("     힐링이 아닌 코드 생성(02_generate) 단계를 확인하세요.")
        _update_parallel_status(
            ParallelStatus.ERROR, path=state_path,
            extra={"error": "pytest exit 5: 테스트 수집 없음 — 코드 생성 문제"},
        )
        sys.exit(0)

    # ── (C) 힐링 ───────────────────────────────────────────────────
    decision = should_heal(pytest_exit_code, failed_count, args.no_heal, heal_count)
    _heal_impossible = False

    if decision == "ok":
        HEAL_CONTEXT_STATE.unlink(missing_ok=True)
        # 힐링을 거쳐 통과한 경우 assertion 무결성 확인
        if heal_count > 0:
            check_assertion_integrity(heal_count, state_path)

    elif decision == "skip":
        print(f"\n[99] 실패 {failed_count}건 -- 힐링 생략 (--no-heal)")
        HEAL_CONTEXT_STATE.unlink(missing_ok=True)

    elif decision == "over_limit":
        print(f"\n[99] 최대 힐링 횟수({MAX_HEAL}회) 초과 -- 수동 수정이 필요합니다.")
        HEAL_CONTEXT_STATE.unlink(missing_ok=True)
        update_state(state_path, lambda fresh: {
            **fresh, "heal_count": heal_count, "heal_failed": True,
        })

    else:  # decision == "heal"
        # P70: heal_count 원자적 증가 (RMW 경쟁 방지)
        update_state(state_path, lambda fresh: {
            **fresh, "heal_count": fresh.get("heal_count", 0) + 1,
        })
        heal_count += 1
        _heal_applied, _heal_impossible = run_heal_cycle(
            report, heal_count, state_path, quick_mode
        )
        if _heal_impossible:
            # P67: 사이트 불가·전체 반복 → HEAL_FAILED
            HEAL_CONTEXT_STATE.unlink(missing_ok=True)
            print("[99] 힐링 불가 (사이트 접근 불가 또는 전체 반복) → HEAL_FAILED 전이")

    # ── (D) HTML 리포트 ────────────────────────────────────────────
    is_final_run = decision in ("ok", "skip", "over_limit") or _heal_impossible
    index_path: Path | None = None
    if is_final_run:
        report_dir = PROJECT_ROOT / "tests" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        index_path = report_dir / f"parallel_index_{ts}.html"
        index_path.write_text(
            build_parallel_html(
                test_results, pytest_summary, now,
                target_groups=args.group,
                skip_messages=parse_skip_messages(report),
            ),
            encoding="utf-8",
        )

    # ── (E) 상태 저장 ──────────────────────────────────────────────
    passed  = pytest_summary.get("passed", 0)
    failed  = pytest_summary.get("failed", 0) + pytest_summary.get("error", 0)
    skipped = pytest_summary.get("skipped", 0)
    total   = passed + failed + skipped
    pass_rate = round(passed / total * 100, 1) if total else 0

    # 그룹별 결과 집계
    group_results: dict = {}
    for nodeid, outcome in test_results.items():
        parts = nodeid.split("/")
        group = None
        for i, p in enumerate(parts):
            if p == GENERATED_DIR.name and i + 1 < len(parts):  # P83
                group = parts[i + 1]
                break
        if not group:
            continue
        if group not in group_results:
            group_results[group] = {"passed": 0, "failed": 0, "skipped": 0, "tests": []}
        if outcome == "passed":
            group_results[group]["passed"] += 1
        elif outcome == "skipped":
            group_results[group]["skipped"] += 1
        else:
            group_results[group]["failed"] += 1
        group_results[group]["tests"].append({
            "nodeid":  nodeid,
            "name":    nodeid.split("::")[-1] if "::" in nodeid else nodeid,
            "passed":  outcome == "passed",
            "outcome": outcome,
        })

    # 최종 status 결정
    if failed == 0:
        _new_status = ParallelStatus.DONE
    elif decision == "skip":
        _new_status = ParallelStatus.HEAL_FAILED   # P72
    elif decision == "over_limit":
        _new_status = ParallelStatus.HEAL_FAILED
    elif _heal_impossible:
        _new_status = ParallelStatus.HEAL_FAILED   # P67
    else:
        _new_status = ParallelStatus.HEAL_NEEDED

    _new_execution_result = {
        "passed":      passed,
        "failed":      failed,
        "skipped":     skipped,
        "total":       total,
        "pass_rate":   pass_rate,
        "report_path": str(index_path.relative_to(PROJECT_ROOT)) if index_path else None,
        "report_name": index_path.name if index_path else None,
        "group_results": group_results,
        "executed_at": now,
        "heal_count":  heal_count,
    }

    update_state(state_path, lambda fresh: {
        **fresh,
        "groups":           args.group or [],
        "execution_result": _new_execution_result,
        "status":           _new_status,
    })

    # 실행 이력
    _duration = round(_time.monotonic() - _start_time, 1)
    groups_list = list(group_results.keys()) if group_results else (args.group or [])
    append_run_history({
        "timestamp":  now,
        "pipeline":   "quick" if quick_mode else "parallel",
        "groups":     groups_list,
        "passed":     passed,
        "failed":     failed,
        "skipped":    skipped,
        "total":      total,
        "pass_rate":  pass_rate,
        "heal_count": heal_count,
        "first_pass": failed == 0 and heal_count == 0,
        "duration_sec": _duration,
    })

    # ── (F) 요약 출력 ──────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  QA Report Generated")
    print("=" * 60)
    print(f"  Total   : {total}")
    print(f"  Passed  : {passed}")
    print(f"  Failed  : {failed}")
    if skipped:
        print(f"  Skipped : {skipped}")
    print()
    print(f"  Tests  : {GENERATED_DIR}")
    print(f"  Report : {index_path or '(힐링 필요 — 실패 수정 후 재실행 시 생성)'}")
    print("=" * 60)
    slog("step_end", step="99_merge", passed=passed, failed=failed,
         total=total, pass_rate=pass_rate, heal_count=heal_count,
         duration_sec=_duration)


if __name__ == "__main__":
    main()
