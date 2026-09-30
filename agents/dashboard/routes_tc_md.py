"""routes_tc_md.py — TC 스튜디오 md 내보내기 API (PRD F7, 로드맵 M6).

미리보기·커밋·롤백 본체는 Import Studio(_import_commit)다. ImportRunError는 409 JSON으로 바꾼다.
"""
from __future__ import annotations

import re

from dash_http import _read_body

_SUITE = r"(?P<suite>[^/]+)"
_RUN = r"(?P<run_id>run_[A-Za-z0-9_-]+)"

MD_ROUTES: list[tuple[str, re.Pattern, str]] = [
    (m, re.compile(p + r"\Z"), h) for m, p, h in [
        ("GET", rf"/api/tc-library/{_SUITE}/export/md/eligibility", "_tcm_eligibility"),
        ("PUT", rf"/api/tc-library/{_SUITE}/md-groups", "_tcm_save_group"),
        ("POST", rf"/api/tc-library/{_SUITE}/export/md", "_tcm_preview"),
        ("POST", rf"/api/tc-library/{_SUITE}/md-exports/{_RUN}/commit", "_tcm_commit"),
        ("POST", rf"/api/tc-library/{_SUITE}/md-exports/{_RUN}/rollback", "_tcm_rollback"),
    ]
]


def _translate(fn):
    """ImportRunError → LibraryError(409) (디스패처가 JSON으로 바꾼다)."""
    from _import_commit import ImportRunError
    from _tc_library import LibraryError
    try:
        return fn()
    except ImportRunError as exc:
        raise LibraryError(str(exc), exc.code, 409) from exc


def _row_view(row: dict) -> dict:
    import _paths
    from _import_commit import _target_for
    target = _target_for(row, _paths.TESTCASES_DIR)
    return {"tc_id": row["tc_id"], "case_id": row.get("case_id", ""), "status": row.get("status"),
            "reason": row.get("reason", ""), "reason_code": row.get("reason_code", ""),
            "file": f"{target.parent.name}/{target.name}", "excluded": row.get("excluded", False),
            "before": row.get("before"), "after": row.get("after")}


class TcMdRoutesMixin:
    def _tcm_eligibility(self, suite: str):
        from _tc_md_export import eligibility
        self._tcl_json({"ok": True, **eligibility(suite)})

    def _tcm_save_group(self, suite: str):
        from _tc_md_export import save_group
        body = _read_body(self)
        cfg = save_group(suite, list(body.get("path") or []), str(body.get("group", "")), str(body.get("code", "")))
        self._tcl_json({"ok": True, "groups": cfg["groups"]})

    def _tcm_preview(self, suite: str):
        from _tc_md_export import preview
        run = _translate(lambda: preview(suite))
        self._tcl_json({"ok": True, "run_id": run["run_id"], "summary": run["summary"],
                        "rows": [_row_view(r) for r in run["rows"]]})

    def _tcm_commit(self, suite: str, run_id: str):
        from _tc_md_export import commit
        skip = [str(t) for t in _read_body(self).get("skip", [])]
        self._tcl_json({"ok": True, **_translate(lambda: commit(suite, run_id, skip))})

    def _tcm_rollback(self, suite: str, run_id: str):
        from _tc_md_export import rollback
        self._tcl_json({"ok": True, **_translate(lambda: rollback(suite, run_id))})
