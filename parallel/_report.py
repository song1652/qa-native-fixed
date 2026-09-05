"""
parallel/_report.py — 병렬 파이프라인 HTML 리포트 생성 (P84)

99_merge.py에서 분리된 build_html 로직.
단일 소스: build_parallel_html() 공개 API 하나.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from report_html import case_row as _case_row, build_report
from _paths import SCREENSHOTS_DIR

try:
    from parse_cases import load_cases as _load_cases
except ImportError:
    _load_cases = None

GENERATED_DIR = Path(__file__).parent.parent / "tests" / "generated"
TESTCASES_DIR = Path(__file__).parent.parent / "testcases"


def _scan_meta_files() -> dict:
    """tests/screenshots/*.meta.json 스캔 → {test_name: meta_dict}.

    P84 리팩토링 후 _report.py에 누락됐던 로직 복원 (05_execute.py와 동일 패턴).
    """
    meta_by_name: dict = {}
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


def _get_artifacts(nodeid: str, outcome: str, meta_by_name: dict) -> dict | None:
    """실패 TC의 artifacts dict 반환. 통과/스킵이거나 meta 없으면 None."""
    if outcome != "failed":
        return None
    test_func = nodeid.split("::")[-1] if "::" in nodeid else nodeid
    meta = meta_by_name.get(test_func, {})
    if not meta:
        return None
    return {
        "screenshot_path": meta.get("screenshot_path", ""),
        "trace_path":      meta.get("trace_path", ""),
        "video_path":      meta.get("video_path", ""),
    }


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

    # 실패 TC의 스크린샷/영상/트레이스 정보 로드 (P84 리팩 후 누락된 부분 복원)
    meta_by_name = _scan_meta_files()

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
                     if case_id and (
                         f"/{case_id}." in k or f"/{case_id}_" in k
                         # tc_CL_01_… 형식: id="CL_01" → /tc_CL_01_ 매칭
                         or f"/tc_{case_id}_" in k
                         # id에 하이픈 포함(예: "CL-01") → 언더스코어 변환 후 재시도
                         or f"/tc_{case_id.replace('-', '_')}_" in k
                     )),
                    None,
                )
                # id 매칭 실패 시 위치 기반 폴백:
                # tc_01_… 형식과 tc_CL_01_… 형식(영문 접두어 + 숫자) 모두 처리.
                if not matched_nodeid:
                    num_str = f"{case_idx + 1:02d}"
                    matched_nodeid = next(
                        (k for k in group_tests
                         if re.search(rf"/tc_[A-Za-z]*_?{num_str}_", k)),
                        None,
                    )
                case_outcome = group_tests.get(matched_nodeid, "failed") if matched_nodeid else "failed"
                if case_outcome == "skipped" and matched_nodeid and matched_nodeid in skip_messages:
                    case = dict(case, skip_reason=skip_messages[matched_nodeid])
                arts = _get_artifacts(matched_nodeid or "", case_outcome, meta_by_name)
                rows_html += _case_row(case, uid, case_outcome, artifacts=arts)
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
                arts = _get_artifacts(nodeid_match or "", outcome, meta_by_name)
                rows_html += _case_row(simple_case, uid, outcome, artifacts=arts)

        if not rows_html:
            rows_html = '<p class="empty-msg">케이스 정보 없음</p>'

        groups_data.append({
            "label": label, "rows_html": rows_html,
            "pass_cnt": g_pass_cnt, "total_cnt": g_total_cnt,
            "all_pass": g_passed, "has_tests": bool(group_tests),
            "skip_cnt": g_skip_cnt,
        })

    return build_report(groups_data, summary, created_at, "Parallel Test Report")
