"""routes_tc_library.py — TC 스튜디오 라이브러리 API (PRD F2·F5·F6, 로드맵 B8~B10).

serve.py의 do_GET/do_POST/do_PATCH/do_DELETE가 맨 앞에서 `_tcl_dispatch`를 호출한다.
경로에 변수가 있어 GET_ROUTES/POST_ROUTES 딕셔너리 대신 정규식 표를 쓴다.
설계 원칙은 routes_import.py와 같다 (serve를 import하지 않음, 경로는 _paths.X).
"""
from __future__ import annotations

import json
import re
import secrets
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote

import _paths
from dash_http import BodyTooLarge, _read_body, _read_raw_body

_SUITE = r"(?P<suite>[^/]+)"
_CASE = r"(?P<case_id>[\w-]+)"
_ID = r"(?P<item_id>[\w-]+)"
MAX_XLSX_BYTES = 25 * 1024 * 1024

ROUTES: list[tuple[str, re.Pattern, str]] = [
    (m, re.compile(p + r"\Z"), h) for m, p, h in [
        ("GET", r"/api/tc-library", "_tcl_suites"),
        ("POST", r"/api/tc-library/import/preview", "_tcl_import_preview"),
        ("POST", r"/api/tc-library/import", "_tcl_import_commit"),
        ("GET", rf"/api/tc-library/{_SUITE}/tree", "_tcl_tree"),
        ("GET", rf"/api/tc-library/{_SUITE}", "_tcl_list"),
        ("GET", rf"/api/tc-library/{_SUITE}/cases/{_CASE}", "_tcl_get_case"),
        ("GET", rf"/api/tc-library/{_SUITE}/cases/{_CASE}/history", "_tcl_history"),
    ]
]


class TcLibraryRoutesMixin:
    """DashboardHandler(TcLibraryRoutesMixin, …, BaseHTTPRequestHandler) 형태로 쓴다."""

    # ── 공통 ──────────────────────────────────────────────────────
    def _tcl_dispatch(self, method: str) -> bool:
        path, _, query = self.path.partition("?")
        if not path.startswith("/api/tc-library"):
            return False
        for route_method, pattern, handler in ROUTES:
            match = pattern.match(path)
            if match and route_method == method:
                params = {k: unquote(v) for k, v in match.groupdict().items()}
                self._tcl_query = {k: v[-1] for k, v in parse_qs(query, keep_blank_values=True).items()}
                try:
                    getattr(self, handler)(**params)
                except BodyTooLarge:
                    self._tcl_json({"ok": False, "error": "요청이 너무 큽니다",
                                    "code": "PAYLOAD_TOO_LARGE"}, 413)
                except Exception as exc:  # LibraryError 계열은 상태 코드를 그대로
                    from _tc_library import LibraryError, RevConflict
                    if not isinstance(exc, LibraryError):
                        raise
                    body = {"ok": False, "error": str(exc), "code": exc.code}
                    if isinstance(exc, RevConflict):
                        body["server_case"] = exc.server_case
                    self._tcl_json(body, exc.status)
                return True
        self._tcl_json({"ok": False, "error": "not found", "code": "NOT_FOUND"}, 404)
        return True

    def _tcl_json(self, payload, status: int = 200) -> None:
        self._serve_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                          "application/json; charset=utf-8", status=status)

    def _tcl_actor(self) -> str:
        return self.headers.get("X-TC-Actor", "web")[:40] or "web"

    # ── 조회 ──────────────────────────────────────────────────────
    def _tcl_suites(self):
        from _tc_library import list_suites
        self._tcl_json({"ok": True, "suites": list_suites()})

    def _tcl_tree(self, suite: str):
        from _tc_library import build_tree, load_cases
        self._tcl_json({"ok": True, "tree": build_tree(load_cases(suite))})

    def _tcl_list(self, suite: str):
        from _tc_library import filter_cases, load_cases
        items = filter_cases(load_cases(suite), self._tcl_query)
        offset = int(self._tcl_query.get("offset", 0))
        limit = min(int(self._tcl_query.get("limit", 200)), 1000)
        self._tcl_json({"ok": True, "total": len(items), "items": items[offset:offset + limit]})

    def _tcl_get_case(self, suite: str, case_id: str):
        from _tc_library import get_case, with_issues
        self._tcl_json({"ok": True, "case": with_issues(get_case(suite, case_id))})

    def _tcl_history(self, suite: str, case_id: str):
        from _tc_library import history
        self._tcl_json({"ok": True, "history": history(suite, case_id)})

    # ── 가져오기 ──────────────────────────────────────────────────
    def _tcl_import_preview(self):
        """본문 = xlsx 원본 바이트 (로드맵 Z3). ?filename= 필수."""
        from _tc_template import analyze_workbook
        from _tc_library import LibraryError
        filename = Path(self._tcl_query.get("filename", "")).name
        if not filename.lower().endswith(".xlsx"):
            raise LibraryError(".xlsx 파일만 가져올 수 있습니다", "UNSUPPORTED_FILE")
        data = _read_raw_body(self, MAX_XLSX_BYTES)
        if not data.startswith(b"PK"):
            raise LibraryError("xlsx 형식이 아닙니다", "UNSUPPORTED_FILE")
        preview_id = "imp_" + secrets.token_hex(6)
        upload_dir = _paths.TC_LIBRARY_DIR / "_uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        xlsx = upload_dir / f"{preview_id}.xlsx"
        xlsx.write_bytes(data)
        try:
            profiles = analyze_workbook(xlsx)
        except Exception as exc:
            xlsx.unlink(missing_ok=True)
            raise LibraryError(f"엑셀을 읽을 수 없습니다: {exc}", "UNREADABLE_XLSX") from exc
        (upload_dir / f"{preview_id}.json").write_text(
            json.dumps({"filename": filename}, ensure_ascii=False), encoding="utf-8")
        from _tc_xlsx_import import import_workbook
        sheets = []
        for name, profile in profiles.items():
            cases = import_workbook(xlsx, profiles, [name], {})
            sheets.append({"name": name, "header_row": profile.header_row,
                           "data_start_row": profile.data_start_row, "cases": len(cases),
                           "result_columns": list(profile.result_columns),
                           "warnings": profile.warnings})
        self._tcl_json({"ok": True, "preview_id": preview_id, "filename": filename,
                        "sheets": sheets})

    def _tcl_import_commit(self):
        from _tc_library import LibraryError, import_cases, save_template
        from _tc_template import analyze_workbook
        from _tc_xlsx_import import import_workbook
        body = _read_body(self)
        preview_id = str(body.get("preview_id", ""))
        if not re.fullmatch(r"imp_[0-9a-f]{12}", preview_id):
            raise LibraryError("미리보기 id가 올바르지 않습니다", "INVALID_PREVIEW")
        upload = _paths.TC_LIBRARY_DIR / "_uploads" / f"{preview_id}.xlsx"
        if not upload.exists():
            raise LibraryError("미리보기가 만료됐습니다. 파일을 다시 선택하세요", "PREVIEW_EXPIRED", 410)
        meta = json.loads(upload.with_suffix(".json").read_text(encoding="utf-8"))
        suite = str(body.get("suite", "")).strip()
        profiles = analyze_workbook(upload)
        sheets = [s for s in body.get("sheets", []) if s in profiles]
        if not sheets:
            raise LibraryError("가져올 시트를 하나 이상 고르세요", "NO_SHEETS")
        prefixes = {k: v for k, v in (body.get("prefixes") or {}).items()
                    if re.fullmatch(r"[A-Z][A-Z0-9]{0,7}", str(v))}
        renamed = upload.with_name(meta["filename"])
        cases = import_workbook(upload, profiles, sheets, prefixes)
        for case in cases:
            case["source_refs"] = [r.replace(upload.name, renamed.name) for r in case["source_refs"]]
        save_template(suite, upload, {s: profiles[s] for s in sheets})
        summary = import_cases(suite, sheets, cases, self._tcl_actor())
        upload.unlink(missing_ok=True)
        upload.with_suffix(".json").unlink(missing_ok=True)
        self._tcl_json({"ok": True, "suite": suite, **summary})
