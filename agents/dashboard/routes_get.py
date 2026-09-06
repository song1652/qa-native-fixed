"""routes_get.py — GetRoutesMixin (serve.py Phase-5 분리).

GET 엔드포인트 핸들러 + 리포트 삭제·정적파일 서빙 메서드.
DashboardHandler가 이 Mixin을 상속받아 사용한다.

설계 원칙:
- 이 모듈은 serve.py를 import하지 않는다 (순환 import 방지).
- __init__ 정의 없음 — MRO에서 BaseHTTPRequestHandler.__init__ 사용.
"""
from __future__ import annotations

import json
from pathlib import Path

from _paths import (
    PIPELINE_STATE as STATE_PATH,
    QUICK_STATE as QUICK_STATE_PATH,
    RUN_HISTORY as RUN_HISTORY_PATH,
    FLAKY_TESTS_PATH,
    HEAL_STATS_PATH,
    REPORTS_DIR,
    TESTCASES_DIR,
    SCREENSHOTS_DIR,
    VIDEOS_DIR,
    DIALOG_PATH,
)
from _validators import is_safe_filename
from dash_state import (
    build_dialogs,
    build_pipeline_state,
    build_batch_state,
    build_pipeline_registry,
    list_pages,
    list_testcase_groups,
    list_generated_groups,
    list_reports,
    load_json,
    _enrich_group_results,
    _is_safe_report_name,
)

# serve.py와 같은 디렉토리에 위치 — static/ 서빙 루트
HERE = Path(__file__).parent


class GetRoutesMixin:
    """GET 핸들러 + 리포트 삭제 + 정적 파일 서빙 메서드 모음.

    DashboardHandler(GetRoutesMixin, ...) 형태로 사용.
    self._serve_bytes / self._serve_json / self._serve_file / self._serve_sse 는
    DashboardHandler infra layer가 제공.
    """

    # ── API GET 핸들러 ────────────────────────────────────────────

    def _get_dialogs(self):
        payload = build_dialogs()
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_events(self):
        self._serve_sse()

    def _get_dialog(self):
        self._serve_json(DIALOG_PATH)

    def _get_state(self):
        self._serve_json(STATE_PATH)

    def _get_pages(self):
        pages = list_pages()
        # project 목록 추출 (중복 제거, 알파벳 정렬 — "기본"은 UI 개념이므로 미포함)
        project_set: set[str] = set()
        for k, v in pages.items():
            if k == "_comment":
                continue
            if isinstance(v, dict) and v.get("project"):
                project_set.add(v["project"])
        project_list = sorted(project_set)
        payload = {"pages": pages, "groups": list_testcase_groups(), "projects": project_list}
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_pipeline_state(self):
        payload = build_pipeline_state()
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_batch_state(self):
        payload = build_batch_state()
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_quick_state(self):
        payload = load_json(QUICK_STATE_PATH) or {}
        payload = _enrich_group_results(payload)
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_run_history(self):
        payload = load_json(RUN_HISTORY_PATH) or []
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_flaky_tests(self):
        payload = load_json(FLAKY_TESTS_PATH) or {"flaky": []}
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_heal_stats(self):
        payload = load_json(HEAL_STATS_PATH) or {}
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_pipeline_registry(self):
        """P45: _pipeline_registry.py 상수를 JSON으로 노출. constants.js가 fetch."""
        payload = build_pipeline_registry()
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_generated_groups(self):
        payload = list_generated_groups()
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_reports(self):
        payload = list_reports()
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    # ── 리포트 삭제 ───────────────────────────────────────────────

    def _post_reports_delete(self):
        """검증된 HTML 리포트 파일을 삭제한다."""
        from dash_http import _read_body
        body = _read_body(self)
        names = body.get("names") if isinstance(body, dict) else None
        if not isinstance(names, list) or not names:
            self._serve_bytes(
                json.dumps({
                    "ok": False,
                    "error": "names must be a non-empty array",
                    "code": "INVALID_REPORT_NAMES",
                }).encode("utf-8"),
                "application/json; charset=utf-8",
                status=400,
            )
            return

        reports_root = REPORTS_DIR.resolve()
        targets: list[tuple[str, Path]] = []
        seen: set[str] = set()
        for name in names:
            if not _is_safe_report_name(name):
                self._serve_bytes(
                    json.dumps({
                        "ok": False,
                        "error": "each report name must be a safe .html filename",
                        "code": "INVALID_REPORT_NAMES",
                    }).encode("utf-8"),
                    "application/json; charset=utf-8",
                    status=400,
                )
                return
            if name in seen:
                continue
            seen.add(name)

            target = reports_root / name
            # 심볼릭 링크는 외부 파일을 가리키는지와 관계없이 리포트로 취급하지 않는다.
            resolved_target = target.resolve(strict=False)
            if (
                target.is_symlink()
                or not resolved_target.is_relative_to(reports_root)
            ):
                self._serve_bytes(
                    json.dumps({
                        "ok": False,
                        "error": "symbolic links are not valid reports",
                        "code": "INVALID_REPORT_NAMES",
                    }).encode("utf-8"),
                    "application/json; charset=utf-8",
                    status=400,
                )
                return
            if target.exists() and not target.is_file():
                self._serve_bytes(
                    json.dumps({
                        "ok": False,
                        "error": "report name does not identify a regular file",
                        "code": "INVALID_REPORT_NAMES",
                    }).encode("utf-8"),
                    "application/json; charset=utf-8",
                    status=400,
                )
                return
            targets.append((name, target))

        deleted = []
        missing = []
        failed = []
        for name, target in targets:
            try:
                target.unlink()
                deleted.append(name)
            except FileNotFoundError:
                missing.append(name)
            except OSError as error:
                failed.append({"name": name, "error": str(error)})

        self._serve_bytes(
            json.dumps({
                "ok": not failed,
                "deleted": deleted,
                "missing": missing,
                "failed": failed,
            }, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    # ── 테스트케이스 조회 ─────────────────────────────────────────

    def _get_testcase(self):
        import re as _re
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        nodeid = qs.get("nodeid", [""])[0]
        if not nodeid:
            self._serve_bytes(
                b'{"ok":false,"error":"nodeid parameter required"}',
                "application/json; charset=utf-8")
            return
        # nodeid 예: tests/heroku/tc_01_login.py::test_login
        #           tests/generated/directcloud/tc_01_login_success.py::test_...
        parts = nodeid.split("/")
        py_file = parts[-1].split("::")[0]  # tc_01_*.py
        # group = 마지막 디렉토리 (generated 건너뜀)
        group = parts[-2] if len(parts) >= 2 else ""
        if group == "generated" and len(parts) >= 3:
            group = parts[-2]  # generated/{group}/file 구조에선 이미 parts[-2]가 group
        if not group or not py_file or ".." in group:
            self._serve_bytes(
                b'{"ok":false,"error":"invalid nodeid"}',
                "application/json; charset=utf-8")
            return
        # tc 번호 추출: tc_01_ / tc_CL_01_ → testcases/{group}/tc_*_.md 검색
        m = _re.match(r"(tc_(?:[A-Za-z]+_)?\d+)_", py_file)
        tc_prefix = m.group(1) if m else None
        tc_dir = TESTCASES_DIR / group
        fpath = None
        if tc_prefix and tc_dir.exists():
            matches = sorted(tc_dir.glob(f"{tc_prefix}_*.md"))
            if matches:
                fpath = matches[0]
        if fpath is None or not fpath.exists():
            self._serve_bytes(
                json.dumps({"ok": False, "error": f"tc file not found for {py_file}"}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return
        content = fpath.read_text(encoding="utf-8")
        self._serve_bytes(
            json.dumps({"ok": True, "content": content, "file": fpath.name}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    # ── 파일 서빙 헬퍼 ────────────────────────────────────────────

    def _get_report_file(self, path: str):
        from urllib.parse import unquote

        fname = unquote(path[len("/reports/"):])
        if not _is_safe_report_name(fname):
            self.send_response(403)
            self.end_headers()
            return
        reports_root = REPORTS_DIR.resolve()
        fpath = reports_root / fname
        resolved_path = fpath.resolve(strict=False)
        if (
            not fpath.is_symlink()
            and resolved_path.is_relative_to(reports_root)
            and fpath.is_file()
        ):
            try:
                content = fpath.read_bytes()
            except OSError:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("X-XSS-Protection", "0")
            self.send_header("Content-Security-Policy",
                             "default-src 'self' https:; "
                             "script-src 'unsafe-inline'; "
                             "style-src 'unsafe-inline' https:; "
                             "font-src 'self' https: data:; "
                             "img-src 'self' data: blob:; "
                             "media-src 'self' blob:")
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def _get_artifact_file(self, path: str, prefix: str, base_dir: Path, content_type: str):
        """screenshots / videos 등 아티팩트 파일 서빙."""
        fname = path[len(prefix):]
        if not is_safe_filename(fname):
            self.send_response(403)
            self.end_headers()
            return
        fpath = base_dir / fname
        if fpath.exists() and fpath.is_file():
            self._serve_file(fpath, content_type)
        else:
            self.send_response(404)
            self.end_headers()

    def _get_static_file(self, path: str):
        rel = path[len("/static/"):]
        # P66: ".." 단독 검사는 절대경로 주입을 막지 못함 → resolve 후 봉쇄
        _static_root = (HERE / "static").resolve()
        fpath = (_static_root / rel).resolve()
        if not fpath.is_relative_to(_static_root):
            self.send_response(403)
            self.end_headers()
            return
        if fpath.exists() and fpath.is_file():
            ext = fpath.suffix.lower()
            mime_map = {
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".png": "image/png",
                ".svg": "image/svg+xml",
            }
            content_type = mime_map.get(ext, "application/octet-stream")
            self._serve_file(fpath, content_type)
        else:
            self.send_response(404)
            self.end_headers()
