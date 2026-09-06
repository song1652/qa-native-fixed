"""
QA Agent Dashboard 서버
프로젝트 루트 또는 어디서든 실행 가능:
  python agents/dashboard/serve.py
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import re
import stat
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PORT = 8766
HERE = Path(__file__).parent                    # agents/dashboard/
PROJECT_ROOT = HERE.parent.parent               # qa-native/

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(HERE))               # sibling modules (dash_*.py, routes_*.py)
# .venv site-packages를 sys.path에 추가 (시스템 Python으로 실행해도 패키지 사용 가능)
_venv_sp = PROJECT_ROOT / ".venv" / "lib"
if _venv_sp.exists():
    for _sp in _venv_sp.glob("python*/site-packages"):
        if str(_sp) not in sys.path:
            sys.path.insert(0, str(_sp))
from _python import PYTHON_EXE
from _validators import is_valid_url, is_valid_group_name, is_safe_filename
from _pipeline_registry import (
    Step, ParallelStatus, make_initial_pipeline_state, PIPELINE_STEP_DEFS,
    STEP_COMPAT, PARALLEL_STEP_LABELS,  # P58: 단일 소스에서 임포트
    RESETTABLE_PARALLEL_STATUSES,       # M-4(P121): heal_count 리셋 정책 단일 소스
    STEP_DEF_BY_NAME,                   # M-2(P134): step_labels first-wins 일관성
)
# 상태 파일 경로 + 안전한 쓰기 함수는 _paths.py가 단일 소스다 (#25).
# 예전엔 이 파일이 자체 STATE_PATH 등을 재선언하고 _safe_write_json/
# _safe_update_json을 따로 구현했는데, 그 사본은 (a) 락 획득 실패를 무시하고
# 진행했고 (b) FSM 전이 검증을 안 거쳐 대시보드로 상태를 조작하면 CLI 경로의
# 안전장치가 전부 우회됐다. 이름은 기존 호출부와의 diff를 줄이려고 별칭으로 유지.
from _paths import (
    PIPELINE_STATE as STATE_PATH,
    PARALLEL_STATE as PARALLEL_STATE_PATH,
    QUICK_STATE as QUICK_STATE_PATH,
    RUN_HISTORY as RUN_HISTORY_PATH,
    DISCUSS_STATE as DISCUSS_PATH,
    write_state as _safe_write_json,
    update_state as _safe_update_json,
    reset_state,
    GENERATED_DIR,
    REPORTS_DIR,
    SCREENSHOTS_DIR,
    VIDEOS_DIR,
    HEAL_STATS_PATH,
    FLAKY_TESTS_PATH,
    LOGS_DIR,
    IMPORT_DIR,
    IMPORT_SESSIONS_DIR,
    IMPORT_SNAPSHOTS_DIR,
    PAGES_JSON,
    TESTCASES_DIR,
    DIALOG_PATH,                                                 # Phase-2: _paths 단일 소스
)
from dash_excel import (                                         # Phase-1
    _list_import_files,
    _detect_header_row,
    _list_excel_sheets,
    _parse_excel_sheet,
    _level_to_priority,
    _to_slug,
    _write_tc_files,
)
from dash_state import (                                         # Phase-2
    TEAM_NOTES_HEADER,
    load_json,
    parse_conclusion_items,
    finalize_team_notes,
    _lookup_tc_title,
    _enrich_group_results,
    build_pipeline_state,
    build_batch_state,
    build_pipeline_registry,
    list_pages,
    list_testcase_groups,
    _natural_sort_key,
    list_generated_groups,
    _is_safe_report_name,
    list_reports,
    build_dialogs,
)
from dash_procs import (                                         # Phase-3
    _SPAWNED_PROCS,
    _SPAWNED_PIDS_LOCK,
    _register_spawned_proc,
    _is_script_running,
    _register_spawned_pid,
    _is_spawned_pid,
    _sse_clients,
    _sse_lock,
)
from dash_http import (                                          # Phase-3
    _read_body,
    _read_profiles_locked,
    _update_profiles_locked,
)
from routes_import import ImportRoutesMixin                       # Phase-4
from routes_get import GetRoutesMixin                             # Phase-5
from routes_ops import OpsRoutesMixin                             # Phase-6
LOGS_DIR.mkdir(exist_ok=True)

ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://localhost:8766")
# DNS rebinding 방어: 허용할 Host 헤더 값 목록 (P49)
_allowed_hosts_env = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = (
    {host for host in re.split(r"[\s,]+", _allowed_hosts_env) if host}
    if _allowed_hosts_env
    else {"localhost:8766", "127.0.0.1:8766"}
)

# Remote mode protects process-spawning and reset endpoints by default. Allowlist
# entries are exact paths unless they end in one ``*``, which means literal prefix.
REMOTE_MODE = os.environ.get("REMOTE_MODE", "").lower() in {
    "1", "true", "yes", "on",
}
REMOTE_API_ALLOWLIST = [
    pattern.strip()
    for pattern in os.environ.get("REMOTE_API_ALLOWLIST", "").split(",")
    if pattern.strip()
]

# _safe_write_json/_safe_update_json은 원래 이 파일이 자체 구현했다 (#25).
# 지금은 모듈 상단에서 _paths.write_state/update_state를 같은 이름으로
# import해서 쓴다 — 그래야 락 획득 실패가 조용히 무시되지 않고(TimeoutError로
# 승격) pipeline.json/parallel.json/quick.json 쓰기가 FSM 전이 검증을 받는다.
# (state/pipeline.json·parallel.json을 "init"/""로 되돌리는 리셋 핸들러는
# 예외 — FSM 규칙상 모든 상태에서 init으로 못 돌아가므로 검증을 우회하는
# reset_state()를 별도로 쓴다. 아래 _post_*_reset 참조.)


class DashboardHandler(                                            # Phase-4/5/6
    ImportRoutesMixin,
    GetRoutesMixin,
    OpsRoutesMixin,
    BaseHTTPRequestHandler,
):

    # ── Route 딕셔너리 ────────────────────────────────────────────
    GET_ROUTES = {
        "/api/dialogs":          "_get_dialogs",
        "/api/events":           "_get_events",
        "/api/dialog":           "_get_dialog",
        "/api/state":            "_get_state",
        "/api/pages":            "_get_pages",
        "/api/pipeline_state":   "_get_pipeline_state",
        "/api/batch_state":      "_get_batch_state",
        "/api/quick_state":      "_get_quick_state",
        "/api/run_history":      "_get_run_history",
        "/api/heal_stats":       "_get_heal_stats",
        "/api/pipeline_registry": "_get_pipeline_registry",
        "/api/flaky_tests":      "_get_flaky_tests",
        "/api/generated_groups": "_get_generated_groups",
        "/api/reports":          "_get_reports",
        "/api/testcase":         "_get_testcase",
        "/api/import/files":     "_get_import_files",
        "/api/import/sheets":    "_get_import_sheets",
        "/api/import/profiles":     "_get_import_profiles_v2",
        "/api/import/preview/csv":  "_get_import_preview_csv",
    }

    POST_ROUTES = {
        "/api/pages/add":          "_post_pages_add",
        "/api/pages/update":       "_post_pages_update",
        "/api/pages/delete":       "_post_pages_delete",
        "/api/reset":              "_post_reset",
        "/api/reset/all":          "_post_reset_all",
        "/api/discuss/start":      "_post_discuss_start",
        "/api/discuss/vote_item":  "_post_discuss_vote_item",
        "/api/discuss/reject":     "_post_discuss_reject",
        "/api/run_qa":             "_post_run_qa",
        "/api/run_qa_parallel":    "_post_run_qa_parallel",
        "/api/run_log":            "_post_run_log",
        "/api/pipeline/reset":     "_post_pipeline_reset",
        "/api/parallel/reset":     "_post_parallel_reset",
        "/api/quick/reset":        "_post_quick_reset",
        "/api/run_merge":          "_post_run_merge",
        "/api/merge_log":          "_post_merge_log",
        "/api/run_quick":          "_post_run_quick",
        "/api/reports/delete":     "_post_reports_delete",
        "/api/import/convert":          "_post_import_convert",
        "/api/import/preview":          "_post_import_preview_v2",
        "/api/import/profiles":         "_post_import_profiles_v2",
        "/api/import/profiles/update":  "_post_import_profiles_update",
        "/api/import/profiles/delete":  "_post_import_profiles_delete",
        "/api/import/commit":           "_post_import_commit_v2",
        "/api/import/rollback":         "_post_import_rollback_v2",
        "/api/heal_stats/reset":        "_post_heal_stats_reset",
        "/api/run_history/reset":  "_post_run_history_reset",
        "/api/discuss/reset":      "_post_discuss_reset",
    }

    # ── Dispatchers ───────────────────────────────────────────────
    def do_GET(self):
        path = self.path.split("?")[0]

        # index
        if path in ("/", "/index.html", "/import-studio"):
            self._serve_file(HERE / "index.html", "text/html; charset=utf-8")
            return

        # exact-match routes
        if path in self.GET_ROUTES:
            getattr(self, self.GET_ROUTES[path])()
            return

        if path.startswith("/api/import/runs/"):
            self._get_import_run_v2(path)
            return

        # prefix routes
        if path.startswith("/reports/"):
            self._get_report_file(path)
            return

        if path.startswith("/screenshots/"):
            self._get_artifact_file(path, "/screenshots/", SCREENSHOTS_DIR, "image/png")
            return

        if path.startswith("/videos/"):
            self._get_artifact_file(path, "/videos/", VIDEOS_DIR, "video/mp4")
            return

        if path.startswith("/static/"):
            self._get_static_file(path)
            return

        self.send_response(404)
        self.end_headers()

    def _check_csrf_origin(self) -> bool:
        """브라우저發 크로스사이트 POST 및 DNS rebinding을 차단한다 (P49).

        1. Host 헤더 검증 (DNS rebinding 방어):
           Host가 ALLOWED_HOSTS 목록에 없으면 거부.
           Origin/Referer 유무와 무관하게 항상 적용.

        2. Origin/Referer 검증 (CSRF 방어):
           Origin이 있으면 ALLOWED_ORIGIN과 비교.
           Referer가 있으면 스킴+호스트만 비교.
           둘 다 없는 요청(curl 등 로컬 CLI)은 Host 검증 통과 시 허용.
        """
        from urllib.parse import urlparse

        # ── (1) Host 헤더 검증 ─────────────────────────────────
        host = self.headers.get("Host", "")
        # Host가 아예 없으면(HTTP/1.0) localhost로 간주해 허용
        if host and host not in ALLOWED_HOSTS:
            return False

        # ── (2) Origin / Referer 검증 ──────────────────────────
        origin = self.headers.get("Origin")
        if origin is None:
            referer = self.headers.get("Referer")
            if referer is None:
                # 헤더 없음 = curl 등 로컬 CLI → Host 검증 통과했으면 허용
                return True
            # Referer는 경로까지 포함하므로 스킴+호스트만 비교
            parsed = urlparse(referer)
            origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme else referer
        if origin == ALLOWED_ORIGIN:
            return True
        # Local users commonly open the same bound server as localhost or
        # 127.0.0.1. Allow only that hostname spelling change, with scheme and
        # port still required to match; remote origins remain blocked.
        allowed = urlparse(ALLOWED_ORIGIN)
        candidate = urlparse(origin)
        loopback_hosts = {"localhost", "127.0.0.1", "[::1]", "::1"}
        return (
            allowed.scheme == candidate.scheme
            and allowed.port == candidate.port
            and allowed.hostname in loopback_hosts
            and candidate.hostname in loopback_hosts
        )

    def _check_remote_allowlist(self, path: str) -> bool:
        """Apply the remote-mode exact/literal-prefix mutation allowlist."""
        if not REMOTE_MODE:
            return True

        is_run = path.startswith("/api/run_")
        is_reset = (
            path == "/api/reset"
            or path.startswith("/api/reset/")
            or path.endswith("/reset")
        )
        if not (is_run or is_reset):
            return True

        for pattern in REMOTE_API_ALLOWLIST:
            if pattern.endswith("*"):
                if path.startswith(pattern[:-1]):
                    return True
            elif path == pattern:
                return True
        return False

    def do_POST(self):
        path = self.path.split("?")[0]
        if not self._check_csrf_origin():
            self.send_response(403)
            self.end_headers()
            return
        if not self._check_remote_allowlist(path):
            content = json.dumps(
                {
                    "ok": False,
                    "error": (
                        "remote mode blocks this endpoint unless allowlisted: "
                        f"{path}"
                    ),
                },
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(403)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        try:
            if path.startswith("/api/import/runs/") and path.endswith("/rollback"):
                self._post_import_run_rollback_v2(path)
                return
            if path in self.POST_ROUTES:
                getattr(self, self.POST_ROUTES[path])()
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            import traceback
            traceback.print_exc()
            msg = json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False).encode("utf-8")
            try:
                msg = json.dumps({"ok": False, "error": "internal server error",
                                  "code": "INTERNAL_ERROR"}, ensure_ascii=False).encode("utf-8")
                self._serve_bytes(msg, "application/json; charset=utf-8", status=500)
            except Exception:
                pass

    def do_DELETE(self):
        """REST-compatible mapping profile deletion."""
        path = self.path.split("?")[0]
        if not self._check_csrf_origin():
            self.send_response(403)
            self.end_headers()
            return
        prefix = "/api/import/profiles/"
        if path.startswith(prefix):
            self._delete_import_profile_v2(path[len(prefix):])
            return
        self.send_response(404)
        self.end_headers()

    def do_PUT(self):
        """REST-compatible mapping profile update."""
        path = self.path.split("?")[0]
        if not self._check_csrf_origin():
            self.send_response(403)
            self.end_headers()
            return
        prefix = "/api/import/profiles/"
        if path.startswith(prefix):
            self._put_import_profile_v2(path[len(prefix):])
            return
        self.send_response(404)
        self.end_headers()

    # ── Infrastructure helpers ────────────────────────────────────
    def _serve_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        q: queue.Queue = queue.Queue(maxsize=10)
        with _sse_lock:
            _sse_clients.append(q)

        def send(data: str):
            self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
            self.wfile.flush()

        try:
            # 연결 즉시 현재 상태 전송
            send(json.dumps(build_dialogs(), ensure_ascii=False))
            while True:
                try:
                    q.get(timeout=15)
                    send(json.dumps(build_dialogs(), ensure_ascii=False))
                except queue.Empty:
                    # keepalive
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except Exception:
            pass
        finally:
            with _sse_lock:
                if q in _sse_clients:
                    _sse_clients.remove(q)

    def _serve_file(self, path: Path, content_type: str):
        if path.exists():
            content = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            if "html" in content_type:
                self.send_header("X-XSS-Protection", "0")
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_json(self, path: Path):
        content = path.read_bytes() if path.exists() else b'{"pipeline_url":"","started_at":"","sessions":[]}'
        self._serve_bytes(content, "application/json; charset=utf-8")

    def _serve_bytes(self, content: bytes, content_type: str, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


class ReusableHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    allow_reuse_port = True


def _is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    import socket
    check_host = "127.0.0.1" if host in ("", "0.0.0.0") else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((check_host, port)) == 0


def main():
    parser = argparse.ArgumentParser(description="QA Agent Dashboard Server")
    parser.add_argument(
        "--host", default="127.0.0.1", help="bind host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=PORT, help=f"port (default: {PORT})"
    )
    args = parser.parse_args()
    host = args.host
    port = args.port

    display_host = (
        "localhost" if host in ("", "0.0.0.0", "127.0.0.1") else host
    )
    global ALLOWED_HOSTS, ALLOWED_ORIGIN
    if not os.environ.get("ALLOWED_HOSTS") and (host != "127.0.0.1" or port != PORT):
        ALLOWED_HOSTS = {
            f"localhost:{port}",
            f"127.0.0.1:{port}",
            f"{host}:{port}",
        }
    if not os.environ.get("ALLOWED_ORIGIN") and (host != "127.0.0.1" or port != PORT):
        ALLOWED_ORIGIN = f"http://{display_host}:{port}"

    if _is_port_in_use(port, host):
        url = f"http://{display_host}:{port}"
        print(f"[Dashboard] 이미 실행 중: {url}")
        webbrowser.open(url)
        return
    server = ReusableHTTPServer((host, port), DashboardHandler)
    url = f"http://{display_host}:{port}"
    print(f"[Dashboard] 서버 시작: {url}")
    print("[Dashboard] 종료: Ctrl+C")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Dashboard] 서버 종료")


if __name__ == "__main__":
    main()
