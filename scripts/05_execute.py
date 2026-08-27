"""
Step 5 -- 테스트 실행
LLM 없음. pytest 실행 후 결과를 state/pipeline.json에 저장.
커스텀 다크 테마 HTML 리포트 생성 (report_html.py 공통 모듈 사용).
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime

from _python import PYTHON_EXE
from _paths import (
    PIPELINE_STATE, PROJECT_ROOT, read_state, update_state, append_run_history,
    SCREENSHOTS_DIR, VIDEOS_DIR,
)
from _constants import DEFAULT_GENERATED_FILE, MAX_PYTEST_WORKERS
from _pipeline_registry import Step  # P68: Step 상수 사용 — 문자열 리터럴 대신
from result_parser import parse_results, parse_skip_messages, parse_durations
from structured_log import slog
from report_html import case_row as _case_row, build_report

TESTCASES_DIR = PROJECT_ROOT / "testcases"
TRACES_DIR = PROJECT_ROOT / "tests" / "traces"


def _scan_meta_files() -> dict:
    """tests/screenshots/*.meta.json 스캔 → {test_name: meta_dict}."""
    meta_by_name = {}
    if SCREENSHOTS_DIR.exists():
        for meta_file in SCREENSHOTS_DIR.glob("*.meta.json"):
            try:
                m = json.loads(meta_file.read_text(encoding="utf-8"))
                name = m.get("test_name", "")
                if name:
                    meta_by_name[name] = m
            except Exception:
                pass
    return meta_by_name


# ── 케이스 메타데이터 로드 ───────────────────────────────────────


def _load_cases_for_group(group_name: str) -> list:
    """testcases/{group_name}/ 에서 케이스 메타데이터 로드."""
    try:
        from parse_cases import load_cases as _load_cases
    except ImportError:
        return []
    group_dir = TESTCASES_DIR / group_name
    if group_dir.is_dir():
        return _load_cases(str(group_dir))
    return []


# ── 테스트 파일/함수 수 계산 ────────────────────────────────────


def count_test_functions(file_path: str) -> tuple[int, bool]:
    """테스트 파일 수(디렉토리인 경우) 또는 함수 수(단일 파일)와 의존성 여부 반환.
    디렉토리: tc_*.py 파일 수를 케이스 수로 사용 (1파일=1케이스 원칙).
    """
    p = Path(file_path)
    try:
        if p.is_dir():
            # 파일 수를 케이스 수로 사용
            files = [f for f in sorted(p.glob("tc_*.py"))
                     if f.name not in ("__init__.py", "conftest.py")]
            return len(files), False
        tree = ast.parse(p.read_text(encoding="utf-8"))
        funcs = [n for n in tree.body
                 if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
        return len(funcs), len(funcs) > 1
    except Exception:
        return 1, False


# ── 그룹명 추출 ────────────────────────────────────────────────


def _extract_group_name(state: dict) -> str:
    """pipeline.json에서 그룹명(테스트케이스 폴더명) 추출."""
    if state.get("group_dir"):
        return state["group_dir"]

    cases_path = state.get("cases_path", "")
    if cases_path:
        p = Path(cases_path)
        if p.is_dir():
            return p.name
        return p.parent.name

    file_path = state.get("generated_file_path", "")
    if file_path:
        p = Path(file_path)
        parts = p.parts
        if "generated" in parts:
            idx = list(parts).index("generated")
            if idx + 2 < len(parts):
                return parts[idx + 1]

    url = state.get("url", "")
    if url:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        if path_parts:
            return path_parts[-1]
        return parsed.netloc.split(".")[0] if parsed.netloc else "test"

    return "test"


# ── 리포트용 rows_html 생성 ────────────────────────────────────


def _tc_sort_key(nodeid: str) -> int:
    m = re.search(r'tc_(\d+)', nodeid)
    return int(m.group(1)) if m else 9999


def _build_rows_html(test_results: dict, test_cases: list, group_name: str,
                     skip_messages: dict | None = None,
                     durations: dict | None = None,
                     meta_by_name: dict | None = None) -> str:
    """테스트 결과와 케이스 메타데이터를 매칭하여 rows_html 생성."""
    skip_messages = skip_messages or {}
    durations = durations or {}
    meta_by_name = meta_by_name or {}
    rows_html = ""

    def _get_artifacts(nodeid: str, outcome: str) -> tuple:
        """(duration_dict, artifacts_dict) 반환."""
        test_func = nodeid.split("::")[-1] if "::" in nodeid else nodeid
        dur = durations.get(nodeid)
        if outcome != "failed":
            return dur, None
        meta = meta_by_name.get(test_func, {})
        if not meta:
            return dur, None
        return dur, {
            "screenshot_path": meta.get("screenshot_path", ""),
            "trace_path": meta.get("trace_path", ""),
            "video_path": meta.get("video_path", ""),
        }

    if test_cases:
        group_outcome = "passed" if all(v == "passed" for v in test_results.values()) else "failed"
        test_items = sorted(test_results.items(), key=lambda x: _tc_sort_key(x[0]))
        for case_idx, case in enumerate(test_cases):
            uid = f"{group_name}_{case_idx}"
            if case_idx < len(test_items):
                nodeid, outcome = test_items[case_idx]
            else:
                nodeid, outcome = "", group_outcome
            if outcome == "skipped" and nodeid in skip_messages:
                case = dict(case, skip_reason=skip_messages[nodeid])
            dur, arts = _get_artifacts(nodeid, outcome)
            rows_html += _case_row(case, uid, outcome, duration=dur, artifacts=arts)
        # YAML 매핑 없는 추가 TC (예: 데모 TC) 렌더링
        for extra_idx, (nodeid, outcome) in enumerate(test_items[len(test_cases):]):
            uid = f"{group_name}_extra_{extra_idx}"
            simple_case = {
                "title": nodeid.split("::")[-1].replace("_", " ").title() if "::" in nodeid else nodeid,
                "precondition": "",
                "steps": [],
                "expected": "",
            }
            if outcome == "skipped" and nodeid in skip_messages:
                simple_case["skip_reason"] = skip_messages[nodeid]
            dur, arts = _get_artifacts(nodeid, outcome)
            rows_html += _case_row(simple_case, uid, outcome, duration=dur, artifacts=arts)
    else:
        for idx, (nodeid, outcome) in enumerate(sorted(test_results.items(), key=lambda x: _tc_sort_key(x[0]))):
            uid = f"{group_name}_{idx}"
            simple_case = {
                "title": nodeid.split("::")[-1].replace("_", " ").title() if "::" in nodeid else nodeid,
                "precondition": "",
                "steps": [],
                "expected": "",
            }
            if outcome == "skipped" and nodeid in skip_messages:
                simple_case["skip_reason"] = skip_messages[nodeid]
            dur, arts = _get_artifacts(nodeid, outcome)
            rows_html += _case_row(simple_case, uid, outcome, duration=dur, artifacts=arts)

    if not rows_html:
        rows_html = '<p class="empty-msg">케이스 정보 없음</p>'
    return rows_html


# ── 메인 ────────────────────────────────────────────────────────


def generate_report_from_state(state_path: Path) -> None:
    """pytest 재실행 없이 state의 execution_result + json_report로 HTML 리포트만 생성."""
    import json as _json
    state = read_state(state_path)
    execution_result = state.get("execution_result", {})
    json_report_path = execution_result.get("json_report_path", "")

    report = {}
    if json_report_path and Path(json_report_path).exists():
        try:
            report = _json.loads(Path(json_report_path).read_text(encoding="utf-8"))
        except Exception:
            pass

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_dir = PROJECT_ROOT / "tests" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"report_{ts}.html"

    group_name = _extract_group_name(state)
    # 항상 최신 tc_*.md에서 직접 로드 (state.test_cases는 stale title 가능)
    test_cases = _load_cases_for_group(group_name)
    if not test_cases:
        test_cases = state.get("test_cases", [])

    test_results = parse_results(report)
    skip_messages = parse_skip_messages(report)
    durations = parse_durations(report)
    meta_by_name = _scan_meta_files()
    pytest_summary = report.get("summary", {})

    rows_html = _build_rows_html(test_results, test_cases, group_name, skip_messages,
                                 durations=durations, meta_by_name=meta_by_name)
    passed = execution_result.get("passed", 0)
    failed = execution_result.get("failed", 0)
    g_skip_cnt = sum(1 for v in test_results.values() if v == "skipped")
    groups_data = [{
        "label": group_name,
        "rows_html": rows_html,
        "pass_cnt": passed,
        "total_cnt": passed + failed + g_skip_cnt,
        "all_pass": failed == 0,
        "has_tests": bool(test_results),
        "skip_cnt": g_skip_cnt,
    }]
    html_content = build_report(
        groups_data=groups_data,
        summary=pytest_summary,
        created_at=now,
        subtitle="Test Report",
    )
    report_path.write_text(html_content, encoding="utf-8")

    execution_result["report_path"] = str(report_path)
    execution_result["report_name"] = report_path.name
    # read_state 이후 다른 프로세스가 갱신했을 수 있는 다른 필드를 덮어쓰지
    # 않도록, 최신 상태 위에 execution_result만 병합한다 (RMW 경쟁 방지).
    update_state(state_path, lambda fresh: {**fresh, "execution_result": execution_result})

    print()
    print("=" * 55)
    print(f"  HTML 리포트: {report_path}")
    print("=" * 55)


def main():
    parser = argparse.ArgumentParser(
        description="Step 5: 테스트 실행 (pytest + JSON 리포트)"
    )
    parser.add_argument(
        "--no-report", action="store_true",
        help="HTML 리포트 생성 건너뜀 (힐링 중 사용)",
    )
    parser.add_argument(
        "--only-failed", action="store_true",
        help="이전 실행 결과에서 실패한 테스트만 재실행 (힐링 재확인 시 사용)",
    )
    args = parser.parse_args()
    no_report = args.no_report
    only_failed = args.only_failed

    state_path = PIPELINE_STATE
    if not state_path.exists():
        print("[오류] state/pipeline.json 없음.")
        sys.exit(1)

    state = read_state(state_path)

    # C-1(P102): TERMINAL 상태에서 새 실행 시작 시 heal_count 리셋 (99_merge.py:115-124와 동일 정책).
    # 힐링 루프 중(step=heal_needed)에는 발동 안 함 → P99가 막은 무한루프 재발 없음.
    _TERMINAL_STEPS = {Step.DONE, Step.HEAL_FAILED, Step.TIMEOUT}
    if state.get("step") in _TERMINAL_STEPS:
        update_state(state_path, lambda s: {**s, "heal_count": 0})
        state = read_state(state_path)

    # heal_count는 06_heal.py에서만 증가시킴 (이중 증가 방지)

    file_path = state.get("generated_file_path", DEFAULT_GENERATED_FILE)
    if not Path(file_path).exists():
        print(f"[오류] 테스트 파일 없음: {file_path}")
        sys.exit(1)

    if SCREENSHOTS_DIR.exists():
        shutil.rmtree(SCREENSHOTS_DIR, ignore_errors=True)
    if TRACES_DIR.exists():
        shutil.rmtree(TRACES_DIR, ignore_errors=True)
    if VIDEOS_DIR.exists():
        shutil.rmtree(VIDEOS_DIR, ignore_errors=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_dir = PROJECT_ROOT / "tests" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"report_{ts}.html"

    n_funcs, has_dependent = count_test_functions(file_path)
    parallel_opts = []
    # M-3(P109)+L-5(P115): is_spa_group([_group_name])과 동일 로직으로 SPA 판정 통일.
    # 이전 코드는 single_session_hosts(고아 설정, pages.json에 존재하지 않음)를 함께 확인했으나 제거.
    # parallel/_exec.py의 is_spa_group과 동일 조건: pages.json의 spa:true 키만 사용.
    _group_name = _extract_group_name(state)
    _pages_json = PROJECT_ROOT / "config" / "pages.json"
    _pages = json.loads(_pages_json.read_text(encoding="utf-8")) if _pages_json.exists() else {}
    _page_cfg = _pages.get(_group_name, {})
    if isinstance(_page_cfg, str):
        _page_cfg = {}
    _single_session = isinstance(_page_cfg, dict) and _page_cfg.get("spa", False)

    # 표시용 케이스 수: state의 test_cases(테스트 데이터) 우선, 없으면 파일/함수 수 사용
    n_cases = len(state.get("test_cases", [])) or n_funcs

    if n_funcs > 1 and not _single_session:
        dist_mode = "loadfile" if has_dependent else "load"
        n_workers = min(n_funcs, MAX_PYTEST_WORKERS)
        parallel_opts = [f"-n{n_workers}", f"--dist={dist_mode}"]
        print(f"[05] 테스트 실행 중: {file_path}  ({n_cases}개 케이스, 병렬 workers={n_workers}, dist={dist_mode})")
    elif _single_session and n_funcs > 1:
        print(f"[05] 테스트 실행 중: {file_path}  ({n_cases}개 케이스, 단일세션 사이트 → 순차 실행)")
    else:
        print(f"[05] 테스트 실행 중: {file_path}  ({n_cases}개 케이스)")
    slog("step_start", step="05_execute", file_path=file_path,
         n_funcs=n_funcs, no_report=no_report)
    print()

    json_report_path = Path(tempfile.gettempdir()) / f"qa_single_report_{ts}.json"

    # ── --only-failed: 이전 실패 nodeids만 수집 ─────────────────────
    test_targets: list[str] = [str(file_path)]
    if only_failed:
        prev_exec = state.get("execution_result", {})
        prev_json_path = prev_exec.get("json_report_path", "")
        if prev_json_path and Path(prev_json_path).exists():
            try:
                prev_report = json.loads(Path(prev_json_path).read_text(encoding="utf-8"))
                prev_results = parse_results(prev_report)
                failed_ids = [nid for nid, oc in prev_results.items() if oc == "failed"]
            except Exception:
                failed_ids = []
            if failed_ids:
                test_targets = failed_ids
                parallel_opts = []   # 소수 재실행 — 병렬 불필요
                print(f"[05] --only-failed: {len(failed_ids)}개 실패 테스트만 재실행")
            else:
                print("[05] --only-failed: 이전 실패 없음 → 전체 실행")
        else:
            print("[05] --only-failed: 이전 리포트 없음 → 전체 실행")

    try:
        result = subprocess.run(
            [
                PYTHON_EXE, "-m", "pytest", *test_targets,
                "--json-report",
                f"--json-report-file={json_report_path}",
                "-v",
                "--tb=short",
            ] + parallel_opts,
            capture_output=False,
            text=True,
            timeout=3600,
        )
    except subprocess.TimeoutExpired:
        print("\n[05] pytest 실행 타임아웃 (3600초 초과)")
        _timeout_result = {
            "passed": 0, "failed": 0, "total": 0,
            "exit_code": -1, "summary": "타임아웃 (3600초 초과)",
            "executed_at": now, "heal_count": state.get("heal_count", 0),
        }
        # pytest 실행(최대 3600초)이 끝난 시점의 최신 상태 위에 이번 실행이
        # 책임지는 필드(step, execution_result)만 병합해 쓴다 — 그 사이 다른
        # 프로세스가 쓴 값을 덮어쓰지 않기 위함(RMW 경쟁 방지).
        update_state(state_path, lambda fresh: {
            **fresh, "step": Step.TIMEOUT, "execution_result": _timeout_result,  # P68: 리터럴 → 상수
        })
        sys.exit(1)

    report = {}
    if json_report_path.exists():
        try:
            report = json.loads(json_report_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    pytest_summary = report.get("summary", {})
    test_results = parse_results(report)  # {nodeid: "passed"|"failed"|"skipped"}

    passed_count = pytest_summary.get("passed", 0)
    failed_count = pytest_summary.get("failed", 0) + pytest_summary.get("error", 0)
    skipped_count = pytest_summary.get("skipped", 0)

    if not test_results:
        passed_count = 0 if result.returncode != 0 else 1
        failed_count = 1 if result.returncode != 0 else 0
        skipped_count = 0

    # ── --only-failed 결과 병합 ──────────────────────────────────────
    # 부분 실행(only-failed) 결과를 이전 전체 실행 결과와 병합해
    # total/passed 카운트가 "3/3"처럼 축소되지 않도록 보정.
    # step="done" / step="heal_needed" 판정은 이 병합 결과 기준.
    _is_partial_run = only_failed and test_targets != [str(file_path)]
    if _is_partial_run:
        prev_exec_full = state.get("execution_result", {})
        prev_total = prev_exec_full.get("total", 0)
        prev_passed = prev_exec_full.get("passed", 0)
        prev_failed = prev_exec_full.get("failed", 0)
        prev_skipped = prev_exec_full.get("skipped", 0)
        if prev_total > 0:
            # 이번 실행에서 통과한 nodeids = 이전에 실패였던 것이 now-passed
            now_passed_ids = {nid for nid, oc in test_results.items() if oc == "passed"}
            newly_fixed = len([nid for nid in test_targets if nid in now_passed_ids])
            still_failed = failed_count
            # 전체 카운트 = 이전 실행 기준 업데이트
            passed_count = prev_passed + newly_fixed
            failed_count = prev_failed - newly_fixed + still_failed
            failed_count = max(0, failed_count)
            skipped_count = prev_skipped

    group_name = _extract_group_name(state)

    # 리포트용: 항상 최신 tc_*.md에서 직접 로드 (state.test_cases는 stale title 가능)
    test_cases = _load_cases_for_group(group_name)
    if not test_cases:
        test_cases = state.get("test_cases", [])

    # report_html.build_report 사용 (병렬 리포트와 동일 형식)
    if not no_report:
        skip_messages = parse_skip_messages(report)
        durations = parse_durations(report)
        meta_by_name = _scan_meta_files()
        rows_html = _build_rows_html(test_results, test_cases, group_name, skip_messages,
                                     durations=durations, meta_by_name=meta_by_name)
        g_pass_cnt = sum(1 for v in test_results.values() if v == "passed")
        g_skip_cnt = sum(1 for v in test_results.values() if v == "skipped")
        g_total_cnt = len(test_results)
        all_pass = failed_count == 0

        groups_data = [{
            "label": group_name,
            "rows_html": rows_html,
            "pass_cnt": g_pass_cnt,
            "total_cnt": g_total_cnt,
            "all_pass": all_pass,
            "has_tests": bool(test_results),
            "skip_cnt": g_skip_cnt,
        }]
        html_content = build_report(
            groups_data=groups_data,
            summary=pytest_summary,
            created_at=now,
            subtitle="Test Report",
        )
        report_path.write_text(html_content, encoding="utf-8")

    total = passed_count + failed_count + skipped_count
    pass_rate = round(passed_count / total * 100, 1) if total else 0
    _parts = [f"{passed_count} passed", f"{failed_count} failed"]
    if skipped_count:
        _parts.append(f"{skipped_count} skipped")
    summary = ", ".join(_parts) if total else "결과 없음"

    group_results = {}
    if test_results:
        gr = {"passed": 0, "failed": 0, "skipped": 0, "tests": []}
        for nodeid, outcome in test_results.items():
            if outcome == "passed":
                gr["passed"] += 1
            elif outcome == "skipped":
                gr["skipped"] += 1
            else:
                gr["failed"] += 1
            gr["tests"].append({
                "nodeid": nodeid,
                "name": nodeid.split("::")[-1] if "::" in nodeid else nodeid,
                "passed": outcome == "passed",
                "outcome": outcome,
            })
        group_results[group_name] = gr

    execution_result = {
        "passed":      passed_count,
        "failed":      failed_count,
        "skipped":     skipped_count,
        "total":       total,
        "pass_rate":   pass_rate,
        "exit_code":   result.returncode,
        "summary":     summary,
        "report_path": str(report_path) if not no_report else "",
        "report_name": report_path.name if not no_report else "",
        "group_results": group_results,
        "executed_at": now,
        "heal_count":  state.get("heal_count", 0),
        "json_report_path": str(json_report_path),
    }

    _new_step = Step.HEAL_NEEDED if failed_count > 0 else Step.DONE  # P68: 리터럴 → 상수
    # pytest 실행(최대 3600초)이 끝난 시점의 최신 상태 위에 이번 실행이
    # 책임지는 필드(step, execution_result)만 병합해 쓴다 — read_state 시점의
    # 오래된 state 스냅샷으로 다른 프로세스의 갱신을 덮어쓰지 않기 위함.
    update_state(state_path, lambda fresh: {
        **fresh, "step": _new_step, "execution_result": execution_result,
    })
    state["step"] = _new_step
    state["execution_result"] = execution_result
    slog("step_end", step="05_execute", passed=passed_count,
         failed=failed_count, total=total, pass_rate=pass_rate)

    # 테스트별 pass/fail/skip 결과 (flaky 감지용)
    per_test_results = {
        nid.split("::")[-1] if "::" in nid else nid: (
            "pass" if oc == "passed" else ("skip" if oc == "skipped" else "fail")
        )
        for nid, oc in test_results.items()
    } if test_results else {}

    append_run_history({
        "timestamp": now,
        "pipeline": "single",
        "group": state.get("group_dir", "unknown"),
        "passed": passed_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "total": total,
        "pass_rate": pass_rate,
        "heal_count": state.get("heal_count", 0),
        "first_pass": state.get("heal_count", 0) == 0 and failed_count == 0,
        "duration_sec": None,
        "per_test_results": per_test_results,
    })

    print()
    print("=" * 55)
    all_pass = failed_count == 0
    status = "성공" if all_pass else "실패"
    print(f"  테스트 {status}: {summary}")
    if not no_report:
        print(f"  HTML 리포트: {report_path}")
    else:
        print("  (힐링 중 -- 리포트 생성 건너뜀)")
    print("=" * 55)


if __name__ == "__main__":
    main()
