"""
parallel/_report.py — 병렬 파이프라인 HTML 리포트 생성 (P84)

99_merge.py에서 분리된 build_html 로직.
단일 소스: build_parallel_html() 공개 API 하나.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from report_html import case_row as _case_row, build_report

try:
    from parse_cases import load_cases as _load_cases
except ImportError:
    _load_cases = None

GENERATED_DIR = Path(__file__).parent.parent / "tests" / "generated"
TESTCASES_DIR = Path(__file__).parent.parent / "testcases"


def _natural_sort_key(p: Path) -> list:
    """파일명을 숫자 기준으로 정렬하는 키 (tc_10 > tc_9 보장)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", p.name)]


def _load_cases_for_group(group_name: str) -> list:
    """testcases/{group_name}/ 에서 케이스 메타데이터 로드."""
    if not _load_cases:
        return []
    group_dir = TESTCASES_DIR / group_name
    if group_dir.is_dir():
        return _load_cases(str(group_dir))
    return []


def _scan_generated_groups() -> dict[str, list[Path]]:
    """tests/generated/ 하위 그룹별 파일 목록 반환 (자연 정렬)."""
    groups: dict[str, list[Path]] = defaultdict(list)
    if not GENERATED_DIR.exists():
        return groups
    for group_dir in sorted(GENERATED_DIR.iterdir(), key=_natural_sort_key):
        if not group_dir.is_dir() or group_dir.name.startswith("."):
            continue
        for f in sorted(
            (f for f in group_dir.glob("*.py")
             if f.name not in ("conftest.py", "__init__.py")),
            key=_natural_sort_key,
        ):
            groups[group_dir.name].append(f)
    return groups


def build_parallel_html(
    test_results: dict,
    summary: dict,
    created_at: str,
    target_groups: list[str] | None = None,
    skip_messages: dict | None = None,
) -> str:
    """그룹별 테스트 결과를 HTML 리포트 문자열로 반환.

    Args:
        test_results:  {nodeid: "passed"|"failed"|"skipped"}
        summary:       pytest JSON summary dict
        created_at:    실행 시각 문자열 (표시용)
        target_groups: 특정 그룹만 포함할 때. None이면 전체.
        skip_messages: {nodeid: skip_reason} — 스킵 이유 표시용.

    Returns:
        완성된 HTML 문자열.
    """
    skip_messages = skip_messages or {}
    groups = _scan_generated_groups()
    if target_groups:
        groups = {k: v for k, v in groups.items() if k in target_groups}

    groups_data = []
    for label, files in groups.items():
        group_tests = {
            k: v for k, v in test_results.items()
            if f"/{label}/" in k or f"\\{label}\\" in k
        }
        g_pass_cnt = sum(1 for v in group_tests.values() if v == "passed")
        g_skip_cnt = sum(1 for v in group_tests.values() if v == "skipped")
        g_total_cnt = len(group_tests)
        g_passed = not any(v == "failed" for v in group_tests.values()) if group_tests else False

        cases = _load_cases_for_group(label)
        rows_html = ""
        if cases:
            for case_idx, case in enumerate(cases):
                uid = f"{label}_{case_idx}"
                case_id = case.get("id", "")
                matched_nodeid = next(
                    (k for k in group_tests
                     if case_id and (f"/{case_id}." in k or f"/{case_id}_" in k)),
                    None,
                )
                # id(예: "CL-01")가 nodeid 패턴(tc_01_...)과 다를 때 위치 기반 폴백.
                if not matched_nodeid:
                    tc_prefix = f"/tc_{case_idx + 1:02d}_"
                    matched_nodeid = next(
                        (k for k in group_tests if tc_prefix in k), None
                    )
                case_outcome = group_tests.get(matched_nodeid, "failed") if matched_nodeid else "failed"
                if case_outcome == "skipped" and matched_nodeid and matched_nodeid in skip_messages:
                    case = dict(case, skip_reason=skip_messages[matched_nodeid])
                rows_html += _case_row(case, uid, case_outcome)
        else:
            for file_idx, f in enumerate(sorted(files, key=_natural_sort_key)):
                uid = f"{label}_{file_idx}"
                nodeid_match = next(
                    (k for k in test_results if f.stem in k), None
                )
                outcome = test_results.get(nodeid_match, "failed") if nodeid_match else "failed"
                simple_case = {
                    "title": f.stem.replace("_", " ").title(),
                    "precondition": "", "steps": [], "expected": "",
                }
                if outcome == "skipped" and nodeid_match and nodeid_match in skip_messages:
                    simple_case["skip_reason"] = skip_messages[nodeid_match]
                rows_html += _case_row(simple_case, uid, outcome)

        if not rows_html:
            rows_html = '<p class="empty-msg">케이스 정보 없음</p>'

        groups_data.append({
            "label": label, "rows_html": rows_html,
            "pass_cnt": g_pass_cnt, "total_cnt": g_total_cnt,
            "all_pass": g_passed, "has_tests": bool(group_tests),
            "skip_cnt": g_skip_cnt,
        })

    return build_report(groups_data, summary, created_at, "Parallel Test Report")
