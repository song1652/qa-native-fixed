"""routes_get.py — GetRoutesMixin (serve.py Phase-5 분리).

GET 엔드포인트 핸들러 + 리포트 삭제·정적파일 서빙 메서드.
DashboardHandler가 이 Mixin을 상속받아 사용한다.

설계 원칙:
- 이 모듈은 serve.py를 import하지 않는다 (순환 import 방지).
- __init__ 정의 없음 — MRO에서 BaseHTTPRequestHandler.__init__ 사용.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import _paths
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


def _resolve_tc_file(nodeid: str):
    """nodeid → (group, test_func, tc_md_path|None). 형식이 잘못되면 None.

    _get_testcase / _get_test_failure_detail이 공유하는 nodeid 해석 로직.
    """
    parts = nodeid.split("/")
    py_file = parts[-1].split("::")[0]  # tc_01_*.py
    test_func = parts[-1].split("::")[-1] if "::" in parts[-1] else ""
    # group = 마지막 디렉토리 (generated 건너뜀)
    group = parts[-2] if len(parts) >= 2 else ""
    if group == "generated" and len(parts) >= 3:
        group = parts[-2]  # generated/{group}/file 구조에선 이미 parts[-2]가 group
    if not group or not py_file or ".." in group:
        return None
    # tc 번호 추출: tc_01_ / tc_CL_01_ → testcases/{group}/tc_*_.md 검색
    m = re.match(r"(tc_(?:[A-Za-z]+_)?\d+)_", py_file)
    tc_prefix = m.group(1) if m else None
    tc_dir = _paths.TESTCASES_DIR / group
    tc_path = None
    if tc_prefix and tc_dir.exists():
        matches = sorted(tc_dir.glob(f"{tc_prefix}_*.md"))
        if matches:
            tc_path = matches[0]
    return group, test_func, tc_path


def _find_failure_error_message(nodeid: str) -> str:
    """pipeline/parallel/quick 상태 중 이 nodeid의 실패 요약(error)을 찾아 반환.

    05_execute.py / 99_merge.py가 group_results[].tests[]에 저장한
    짧은 실패 메시지(마지막 트레이스백 줄)를 조회한다. 없으면 빈 문자열.
    """
    for state_path in (_paths.PIPELINE_STATE, _paths.PARALLEL_STATE, _paths.QUICK_STATE):
        data = load_json(state_path) or {}
        group_results = (data.get("execution_result") or {}).get("group_results") or {}
        for group_data in group_results.values():
            for test in group_data.get("tests", []):
                if test.get("nodeid") == nodeid and test.get("error"):
                    return test["error"]
    return ""


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
        self._serve_json(_paths.DIALOG_PATH)

    def _get_state(self):
        self._serve_json(_paths.PIPELINE_STATE)

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
        payload = load_json(_paths.QUICK_STATE) or {}
        payload = _enrich_group_results(payload)
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_run_history(self):
        payload = load_json(_paths.RUN_HISTORY) or []
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_flaky_tests(self):
        payload = load_json(_paths.FLAKY_TESTS_PATH) or {"flaky": []}
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_heal_stats(self):
        payload = load_json(_paths.HEAL_STATS_PATH) or {}
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

        reports_root = _paths.REPORTS_DIR.resolve()
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
        resolved = _resolve_tc_file(nodeid)
        if resolved is None:
            self._serve_bytes(
                b'{"ok":false,"error":"invalid nodeid"}',
                "application/json; charset=utf-8")
            return
        _group, _test_func, fpath = resolved
        py_file = nodeid.split("/")[-1].split("::")[0]
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

    def _get_test_failure_detail(self):
        """GET /api/testcase/failure_detail?nodeid=... — 실패 TC 상세.

        스크린샷·콘솔로그·네트워크실패·trace는 tests/conftest.py가 실패 시
        기록한 meta.json에서, 실패 요약(error)은 05_execute.py/99_merge.py가
        group_results에 저장한 값에서 가져온다. 둘 다 없어도 200으로
        빈 필드를 반환한다 — 아직 실행되지 않았거나 이전 실행 데이터일 뿐이다.
        """
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        nodeid = qs.get("nodeid", [""])[0]
        if not nodeid:
            self._serve_bytes(
                b'{"ok":false,"error":"nodeid parameter required"}',
                "application/json; charset=utf-8")
            return

        resolved = _resolve_tc_file(nodeid)
        if resolved is None:
            self._serve_bytes(
                b'{"ok":false,"error":"invalid nodeid"}',
                "application/json; charset=utf-8")
            return
        group, test_func, tc_path = resolved

        expected = ""
        steps = ""
        if tc_path and tc_path.exists():
            try:
                content = tc_path.read_text(encoding="utf-8")
                m = re.search(r"^##\s*Expected\s*$\n([\s\S]*?)(?=\n##\s|\Z)", content, re.MULTILINE)
                if m:
                    expected = m.group(1).strip()
                m = re.search(r"^##\s*Steps\s*$\n([\s\S]*?)(?=\n##\s|\Z)", content, re.MULTILINE)
                if m:
                    steps = m.group(1).strip()
            except OSError:
                pass

        detail = {
            "ok": True,
            "nodeid": nodeid,
            "group": group,
            "test_name": test_func,
            "steps": steps,
            "expected": expected,
            "url": None,
            "timestamp": None,
            "error_summary": _find_failure_error_message(nodeid),
            "screenshot_url": None,
            "video_url": None,
            "trace_cmd": None,
            "console_errors": [],
            "network_failures": [],
        }

        shot_candidates = []
        if _paths.SCREENSHOTS_DIR.exists():
            shot_candidates = sorted(_paths.SCREENSHOTS_DIR.glob(f"*__{test_func}.png")) \
                or sorted(_paths.SCREENSHOTS_DIR.glob(f"{test_func}.png"))
        if shot_candidates:
            shot_path = shot_candidates[0]
            if is_safe_filename(shot_path.name):
                detail["screenshot_url"] = f"/screenshots/{shot_path.name}"
            meta_path = shot_path.with_suffix("").with_suffix(".meta.json")
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    meta = {}
                detail["url"] = meta.get("url")
                detail["timestamp"] = meta.get("timestamp")
                detail["console_errors"] = meta.get("console_errors") or []
                detail["network_failures"] = meta.get("network_failures") or []
                trace_path = meta.get("trace_path")
                if trace_path and Path(trace_path).exists():
                    detail["trace_cmd"] = f"npx playwright show-trace {trace_path}"
                video_path = meta.get("video_path")
                if video_path and Path(video_path).exists() and is_safe_filename(Path(video_path).name):
                    detail["video_url"] = f"/videos/{Path(video_path).name}"

        self._serve_bytes(
            json.dumps(detail, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    # ── 파일 서빙 헬퍼 ────────────────────────────────────────────

    def _get_report_file(self, path: str):
        from urllib.parse import unquote

        fname = unquote(path[len("/reports/"):])
        if not _is_safe_report_name(fname):
            self.send_response(403)
            self.end_headers()
            return
        reports_root = _paths.REPORTS_DIR.resolve()
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
            body = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                "<style>"
                "body{display:flex;align-items:center;justify-content:center;"
                "height:100vh;margin:0;font-family:'Inter',sans-serif;"
                "background:#08071b;color:#b8b3d0;}"
                ".box{text-align:center;padding:32px;border:1px solid rgba(140,120,220,0.12);"
                "border-radius:16px;background:rgba(18,16,42,0.55);backdrop-filter:blur(12px);}"
                ".icon{font-size:44px;margin-bottom:16px;line-height:1;}"
                ".title{font-size:16px;font-weight:600;color:#f0eff5;margin-bottom:8px;}"
                ".sub{font-size:12px;color:rgba(184,179,208,0.5);font-family:monospace;"
                "word-break:break-all;max-width:320px;margin:0 auto;}"
                "</style></head><body>"
                f"<div class='box'><div class='icon'>🗑️</div>"
                f"<div class='title'>리포트가 삭제되었습니다</div>"
                f"<div class='sub'>{fname}</div></div></body></html>"
            ).encode("utf-8")
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

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
