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

import os
import uuid
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
from _constants import MAX_HEAL, PYTEST_NORMAL_EXIT_CODES  # M-2(P119): 단일 소스
from _pipeline_registry import ParallelStatus, RESETTABLE_PARALLEL_STATUSES  # M-4(P121)
from result_parser import parse_results, parse_skip_messages, parse_failure_messages
from structured_log import slog
from error_policy import classify_error, recovery_for_result, errors_from_report
from run_results import read_execution_result, write_execution_result

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
TRACES_DIR     = PROJECT_ROOT / "tests" / "traces"  # L-7(P147)


# ── 상태 업데이트 헬퍼 ───────────────────────────────────────────────────────


def _update_parallel_status(
    status: str,
    extra: dict | None = None,
    *,
    path: Path | None = None,
    run_id: str | None = None,
) -> None:
    """state/parallel.json(또는 path)의 status 필드를 업데이트 (원자적 RMW).

    Args:
        status: 설정할 새 status 값.
        extra:  추가로 병합할 필드 딕셔너리.
        path:   상태 파일 경로. None이면 PARALLEL_STATE.
                quick 모드에서는 QUICK_STATE를 전달한다 (P41).
    """
    def _mutator(fresh: dict) -> dict:
        if run_id and fresh.get("run_id") not in (None, "", run_id):
            return fresh
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
    parser.add_argument(
        "--no-report", action="store_true",
        help="리포트 생성 생략 (힐링 중 중간 실행 시 사용)",
    )
    args = parser.parse_args()

    _start_time = _time.monotonic()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    run_id = os.environ.get("QA_RUN_ID", "").strip() or "parallel_" + ts

    if (read_execution_result(PROJECT_ROOT, run_id) or {}).get("status") in ("cancelled", "interrupted", "timed_out"):
        print(f"[99] 종료된 실행 — 테스트를 반복하지 않습니다: {run_id}")
        return

    quick_mode = args.quick
    state_path = QUICK_STATE if quick_mode else PARALLEL_STATE

    initial = read_state(state_path)
    inherited = os.environ.get("QA_RUN_ID", "").strip()
    if inherited and initial.get("run_id") not in (None, "", inherited):
        print("[99] 이전 실행 요청 — 새 실행 소유권을 유지합니다")
        return
    def claim(fresh):
        if inherited and fresh.get("run_id") not in (None, "", run_id):
            return fresh
        return {**fresh, "run_id": run_id}
    claimed = update_state(state_path, claim)
    if claimed.get("run_id") != run_id:
        return

    def record_start_failure(error, exit_code=None):
        result = {"run_id": run_id, "status": "failed", "pipeline": "quick" if quick_mode else "parallel",
                  "passed": 0, "failed": 0, "skipped": 0, "total": 0, "pass_rate": 0,
                  "exit_code": exit_code, "error": error, "groups": args.group or [],
                  "report_path": None, "report_name": None, "group_results": {},
                  "executed_at": now, "finished_at": now, "heal_count": 0, "first_pass": False,
                  "recovery": classify_error(error)}
        result["recovery"] = recovery_for_result(result)
        if result["recovery"]["category"] == "interrupted":
            result["status"] = "interrupted"
        saved = write_execution_result(PROJECT_ROOT, run_id, result)
        if saved.get("status") != result["status"]:
            return
        result = saved
        _update_parallel_status(ParallelStatus.ERROR, {"error": error, "execution_result": result}, path=state_path, run_id=run_id)
        append_run_history({**result, "timestamp": now, "duration_sec": round(_time.monotonic() - _start_time, 1)})

    # ── (A) 파일 수집 ──────────────────────────────────────────────
    sorted_files, scope_label = collect_test_files(args.group)
    if not sorted_files:
        record_start_failure("no tests collected: 선택한 그룹에 실행할 테스트 파일이 없습니다", 5)
        return

    slog("step_start", step="99_merge", scope=scope_label,
         file_count=len(sorted_files), quick=quick_mode)
    # L-3(P113): SPA 판정 먼저 수행 후 실행 모드 메시지 출력
    _single_session = is_spa_group(args.group)
    _exec_mode = "순차" if _single_session else "병렬"
    print(f"\n[99] 실행 범위: {scope_label}  ({len(sorted_files)}개 케이스, {_exec_mode} 실행)")

    # 실행별 파일 접두어로 증거를 분리한다. 이전 실행의 리포트 증거는 보존한다.

    # M-4(P110/P121): RESETTABLE 상태에서 새 실행 시작 시 heal_count 리셋.
    # HEAL_NEEDED(힐링 재실행) 상태이면 리셋하지 않아 누적 카운트를 유지.
    # RESETTABLE_PARALLEL_STATUSES는 _pipeline_registry.py 단일 소스 (M-4/P121 통합).
    _pre_run_state = read_state(state_path)
    _prev_run_status = (_pre_run_state or {}).get("status", "")
    if _prev_run_status in RESETTABLE_PARALLEL_STATUSES:
        update_state(state_path, lambda fresh: {**fresh, "heal_count": 0})

    # FSM: TESTING으로 전이 (P41 — done→testing→결과 경로 확보)
    _update_parallel_status(ParallelStatus.TESTING, {"last_run_id": run_id}, path=state_path, run_id=run_id)

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
    # _single_session은 L-3(P113) 수정으로 위쪽(slog 직전)에서 이미 계산됨
    if _single_session:
        print("[99] SPA 사이트 감지 → 단일세션 순차 실행")
    try:
        pytest_exit_code, report = run_pytest(sorted_files, single_session=_single_session, run_id=run_id)
    except Exception as exc:
        record_start_failure(f"{type(exc).__name__}: {exc}")
        return
    test_results    = parse_results(report)
    pytest_summary  = report.get("summary", {})
    failed_count    = pytest_summary.get("failed", 0) + pytest_summary.get("error", 0)

    # 실행 메타데이터만 있는 리포트는 테스트 측정 증거가 아니다.
    # 정상 종료코드라도 측정 결과·수집 오류가 모두 없으면 통과로 기록하지 않는다.
    if not test_results and not errors_from_report(report):
        print(f"[99] 측정된 테스트 결과 없음 (exit={pytest_exit_code}) — ERROR 처리")
        record_start_failure("no tests collected" if pytest_exit_code == 5 else
                             "pytest usage error" if pytest_exit_code == 4 else
                             f"pytest exit {pytest_exit_code}: 실행 결과를 수집하지 못했습니다", pytest_exit_code)
        sys.exit(0)

    # P73: pytest exit 5 = 수집된 테스트 없음
    if pytest_exit_code == 5 and failed_count == 0:
        print("\n[99] ⚠️ pytest 종료코드 5 — 수집된 테스트 없음")
        print("     tests/generated/ 디렉토리가 비어있거나 tc_*.py 파일이 없습니다.")
        print("     힐링이 아닌 코드 생성(02_generate) 단계를 확인하세요.")
        record_start_failure("no tests collected: 코드 생성과 선택 그룹을 확인하세요", 5)
        sys.exit(0)

    # 복구는 측정된 이 실행의 오류만 참조한다.
    measured = {"run_id": run_id, "status": "failed" if pytest_exit_code else "passed",
                "errors": errors_from_report(report), "executed_at": now, "exit_code": pytest_exit_code,
                "invocation_id": (report.get("_qa_execution") or {}).get("invocation_id"),
                "passed": pytest_summary.get("passed", 0), "failed": failed_count,
                "json_report_path": (report.get("_qa_execution") or {}).get("json_report_path"),
                "pipeline": "quick" if quick_mode else "parallel", "groups": args.group or []}
    measured["recovery"] = recovery_for_result(measured)
    measured = write_execution_result(PROJECT_ROOT, run_id, measured)
    if measured["status"] in ("cancelled", "interrupted", "timed_out"):
        return
    update_state(state_path, lambda fresh: {**fresh, "last_run_id": run_id, "execution_result": measured}
                 if fresh.get("run_id") == run_id else fresh)
    if read_state(state_path).get("run_id") != run_id:
        print("[99] 실행 소유권 변경 — 이전 실행의 후속 작업 중단")
        return

    # ── (C) 힐링 ───────────────────────────────────────────────────
    decision = should_heal(pytest_exit_code, failed_count, args.no_heal, heal_count)
    _heal_impossible = False
    recovery = recovery_for_result({"errors": errors_from_report(report), "exit_code": pytest_exit_code})
    if decision == "heal" and not recovery["can_heal"]:
        decision = "blocked"
        _heal_impossible = True
        HEAL_CONTEXT_STATE.unlink(missing_ok=True)
        print(f"[99] 자동 복구 중단: {recovery['message']}")

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
        update_state(state_path, lambda fresh: {  # L-3(P125): heal_failed 죽은 필드 제거
            **fresh, "heal_count": heal_count,
        })

    elif decision == "heal":
        # P70: heal_count 원자적 증가 (RMW 경쟁 방지)
        update_state(state_path, lambda fresh: {
            **fresh, "heal_count": fresh.get("heal_count", 0) + 1,
        })
        heal_count += 1
        _heal_applied, _heal_impossible, _auto_all_fixed = run_heal_cycle(
            report, heal_count, state_path, quick_mode
        )
        if _heal_impossible:
            # P67: 사이트 불가·전체 반복 → HEAL_FAILED
            # 중단 원인과 원본 복원 기록은 보존한다.
            # L-2(P124): "HEAL_FAILED 전이" 직접 출력 제거 — exit code 가드(C-2) 우선 시
            # ERROR가 될 수 있으므로, 최종 상태는 아래 _new_status 결정 후 출력함.
            print("[99] 힐링 불가 (사이트 접근 불가 또는 전체 반복)")
        elif _auto_all_fixed:
            # H-2(P132): auto_heal 전건 성공 → HEAL_NEEDED 교착 방지.
            # 모든 실패가 자동 수정됐으므로 subagent 힐링 대신 재실행으로 검증한다.
            print("[99] ✅ auto_heal 전건 성공 — 재실행으로 최종 검증 중...")
            pytest_exit_code, report = run_pytest(sorted_files, single_session=_single_session, run_id=run_id)
            test_results   = parse_results(report)
            pytest_summary = report.get("summary", {})
            failed_count   = pytest_summary.get("failed", 0) + pytest_summary.get("error", 0)
            if not test_results and not errors_from_report(report):
                record_start_failure("검증 실행에서 측정된 테스트 결과를 수집하지 못했습니다", pytest_exit_code)
                return
            current_recovery = recovery_for_result({"errors": errors_from_report(report), "exit_code": pytest_exit_code})
            if pytest_exit_code and not current_recovery["can_heal"]:
                decision = "blocked"
                _heal_impossible = True
            if not failed_count:
                HEAL_CONTEXT_STATE.unlink(missing_ok=True)
            else:
                print(f"[99] 재실행 후 {failed_count}건 실패 — 다음 99_merge.py 실행 시 heal context 재생성")

    # ── (D) HTML 리포트 ────────────────────────────────────────────
    is_final_run = decision in ("ok", "skip", "over_limit") or _heal_impossible
    index_path: Path | None = None
    if is_final_run and not args.no_report:
        report_dir = PROJECT_ROOT / "tests" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        index_path = report_dir / f"parallel_index_{ts}.html"
        index_path.write_text(
            build_parallel_html(
                test_results, pytest_summary, now,
                target_groups=args.group,
                skip_messages=parse_skip_messages(report),
                quick_mode=quick_mode,
                evidence_owner=report.get("_qa_execution"),
            ),
            encoding="utf-8",
        )

    # ── (D-2) Jira 자동 이슈 생성 (is_final_run + 실패 있을 때) ──────
    if is_final_run and not args.no_report:
        _jira_failed = pytest_summary.get("failed", 0) + pytest_summary.get("error", 0)
        if _jira_failed:
            try:
                _jira_reporter = PROJECT_ROOT / "scripts" / "jira_reporter.py"
                if _jira_reporter.exists():
                    import importlib.util as _ilu
                    _spec = _ilu.spec_from_file_location("jira_reporter", _jira_reporter)
                    _mod  = _ilu.module_from_spec(_spec)  # type: ignore[arg-type]
                    _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
                    _cfg     = _mod._load_config()
                    _client  = _mod.JiraClient(_cfg)
                    _fails   = _mod._load_failures_from_state(args.group or None)
                    _created = []
                    for _f in _fails:
                        _key = _mod.create_jira_issue(_client, _cfg, _f)
                        if _key:
                            _created.append(_key)
                    if _created:
                        print(f"\n[99] 🐛 Jira 이슈 {len(_created)}건 자동 생성")
                        for _k in _created:
                            print(f"     → {_cfg['base_url']}/browse/{_k}")
            except Exception as _je:
                print(f"[99] ⚠️ Jira 연동 실패 (스킵): {_je}")

    # ── (E) 상태 저장 ──────────────────────────────────────────────
    passed  = pytest_summary.get("passed", 0)
    failed  = pytest_summary.get("failed", 0) + pytest_summary.get("error", 0)
    skipped = pytest_summary.get("skipped", 0)
    total   = passed + failed + skipped
    pass_rate = round(passed / total * 100, 1) if total else 0

    # 그룹별 결과 집계
    group_results: dict = {}
    failure_messages = parse_failure_messages(report)
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
            "error":   failure_messages.get(nodeid, "") if outcome == "failed" else "",
        })

    # 최종 status 결정
    # M-2(P119): PYTEST_NORMAL_EXIT_CODES 기반 강화 — exit 2/3/4에서 partial pass도 ERROR 처리.
    # C-2(P103) 기존 "total==0 and exit!=0" 가드를 포함하는 더 넓은 조건.
    # exit 5(수집 없음)는 위 154-163행에서 이미 처리 후 sys.exit(0) → 여기 도달 안 함.
    if pytest_exit_code not in PYTEST_NORMAL_EXIT_CODES:
        _new_status = ParallelStatus.ERROR
        print(f"[99] 비정상 pytest 종료 (exit {pytest_exit_code}) → ERROR 상태")
    elif failed == 0:
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
        "run_id": run_id,
        "invocation_id": (report.get("_qa_execution") or {}).get("invocation_id"),
        "json_report_path": (report.get("_qa_execution") or {}).get("json_report_path"),
        "status": "passed" if _new_status == ParallelStatus.DONE and pytest_exit_code == 0 else "failed",
        "exit_code": pytest_exit_code,
        "errors": errors_from_report(report),
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
        "heal_decision": decision,
    }

    _new_execution_result["recovery"] = recovery_for_result(_new_execution_result)
    if _new_execution_result["recovery"]["category"] == "interrupted":
        _new_execution_result["status"] = "interrupted"
    _stopped = (read_state(state_path).get("heal_context") or {}).get("recovery_stopped")
    if _stopped:
        _new_execution_result["recovery_stopped"] = True
        _new_execution_result["recovery"] = {**_new_execution_result["recovery"], "can_heal": False,
            "message": (read_state(state_path).get("heal_context") or {}).get("error", "자동 복구 검증 실패 — 변경을 복원하고 추가 실행을 중단했습니다.")}
    _new_execution_result = write_execution_result(PROJECT_ROOT, run_id, {**_new_execution_result, "pipeline": "quick" if quick_mode else "parallel", "groups": args.group or [], "finished_at": datetime.now().isoformat()})
    if _new_execution_result["status"] in ("cancelled", "interrupted", "timed_out"):
        _new_status = ParallelStatus.ERROR
    update_state(state_path, lambda fresh: fresh if fresh.get("run_id") != run_id else {
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
        "run_id": run_id,
        "status": _new_execution_result["status"],
        "recovery": _new_execution_result["recovery"],
        "errors": _new_execution_result["errors"],
        "report_path": _new_execution_result["report_path"],
        "pipeline":   "quick" if quick_mode else "parallel",
        "groups":     groups_list,
        "passed":     passed,
        "failed":     failed,
        "skipped":    skipped,
        "total":      total,
        "pass_rate":  pass_rate,
        "heal_count": heal_count,
        "first_pass": _new_execution_result["status"] == "passed" and heal_count == 0,
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
