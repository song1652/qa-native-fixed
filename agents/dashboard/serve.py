"""
QA Agent Dashboard 서버
프로젝트 루트 또는 어디서든 실행 가능:
  python agents/dashboard/serve.py
"""
from __future__ import annotations

import json
import queue
import re
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
# .venv site-packages를 sys.path에 추가 (시스템 Python으로 실행해도 패키지 사용 가능)
_venv_sp = PROJECT_ROOT / ".venv" / "lib"
if _venv_sp.exists():
    for _sp in _venv_sp.glob("python*/site-packages"):
        if str(_sp) not in sys.path:
            sys.path.insert(0, str(_sp))
from _python import PYTHON_EXE
DIALOG_PATH = PROJECT_ROOT / "agents" / "dialog.json"
STATE_PATH = PROJECT_ROOT / "state" / "pipeline.json"
TEAM_NOTES_PATH = PROJECT_ROOT / "agents" / "team_notes.md"
DISCUSS_PATH = PROJECT_ROOT / "state" / "discuss.json"
PENDING_IMPL_PATH = PROJECT_ROOT / "pending_impl.json"
PARALLEL_STATE_PATH = PROJECT_ROOT / "state" / "parallel.json"
GENERATED_DIR = PROJECT_ROOT / "tests" / "generated"
REPORTS_DIR = PROJECT_ROOT / "tests" / "reports"
QUICK_STATE_PATH = PROJECT_ROOT / "state" / "quick.json"
RUN_HISTORY_PATH = PROJECT_ROOT / "state" / "run_history.json"
HEAL_STATS_PATH = PROJECT_ROOT / "state" / "heal_stats.json"
FLAKY_TESTS_PATH = PROJECT_ROOT / "state" / "flaky_tests.json"
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
IMPORT_DIR = PROJECT_ROOT / "import"

ALLOWED_ORIGIN = "http://localhost:8766"

# ── SSE 클라이언트 관리 ────────────────────────────────────────
_sse_clients: list[queue.Queue] = []
_sse_lock = threading.Lock()


def _sse_notify():
    """dialog.json 변경 시 모든 SSE 클라이언트에 알림."""
    with _sse_lock:
        dead = []
        for q in _sse_clients:
            try:
                q.put_nowait("update")
            except queue.Full:
                dead.append(q)
        for q in dead:
            _sse_clients.remove(q)


def _watch_files():
    """dialog.json / state/discuss.json mtime을 0.3초마다 감시."""
    watched = [DIALOG_PATH, DISCUSS_PATH, STATE_PATH, PARALLEL_STATE_PATH,
               QUICK_STATE_PATH]
    last_mtimes = {p: 0.0 for p in watched}
    while True:
        for p in watched:
            try:
                mtime = p.stat().st_mtime if p.exists() else 0.0
                if mtime != last_mtimes[p]:
                    last_mtimes[p] = mtime
                    _sse_notify()
            except Exception:
                pass
        time.sleep(0.3)


# 파일 감시 스레드 시작
threading.Thread(target=_watch_files, daemon=True).start()

TEAM_NOTES_HEADER = (
    "# 팀 결정 사항\n\n"
    "> **독자**: 심의 Agent — 팀 토론 결론 누적. 토론 시 중복 결론 방지 목적으로 참조.\n\n"
    "---\n"
)


def load_json(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[Dashboard] JSON 파싱 실패: {path} — {e}")
            return None
    return None


def parse_conclusion_items(conclusion: str) -> list:
    """결론 마크다운을 투표 가능한 개별 항목으로 파싱."""
    items = []

    # 1) ### 소제목 파싱
    for m in re.finditer(r'^###\s+(.+?)\n([\s\S]*?)(?=^###\s|\Z)', conclusion, re.MULTILINE):
        title = m.group(1).strip()
        body  = re.sub(r'\n?---+\s*$', '', m.group(2)).strip()
        items.append({"id": len(items), "title": title, "text": body, "status": "pending"})

    # 2) 번호 목록 파싱 (1. **title**: body)
    if not items:
        for m in re.finditer(r'^\d+\.\s+(.+)$', conclusion, re.MULTILINE):
            text = m.group(1).strip()
            bold = re.match(r'\*\*(.+?)\*\*[:\s]*(.*)', text)
            title = bold.group(1).strip() if bold else text[:70]
            items.append({"id": len(items), "title": title, "text": text, "status": "pending"})

    # 3) 괄호 번호 패턴 파싱: (1) ... (2) ... 또는 인라인 구분
    if not items:
        parts = re.split(r'\s*\((\d+)\)\s*', conclusion)
        # parts: ['앞부분', '1', '내용1', '2', '내용2', ...]
        if len(parts) >= 3:
            for i in range(1, len(parts) - 1, 2):
                text = parts[i + 1].strip().rstrip('.')
                if not text:
                    continue
                # 첫 문장이나 키워드를 제목으로 추출
                title_match = re.match(r'^(.+?)[.:\-—]', text)
                title = title_match.group(1).strip() if title_match else text[:70]
                items.append({"id": len(items), "title": title, "text": text, "status": "pending"})

    # 4) fallback
    if not items:
        items.append({"id": 0, "title": "전체 결론", "text": conclusion, "status": "pending"})

    return items


def finalize_team_notes(discuss: dict):
    """승인된 항목만 team_notes.md에 덮어쓰기 + pending_impl.json 생성."""
    import datetime
    items = discuss.get("conclusion_items", [])
    approved = [i for i in items if i["status"] == "approved"]
    topic = discuss.get("topic", "")
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    content = TEAM_NOTES_HEADER
    if approved:
        content += f"\n## {topic}\n> 결정일: {today}\n\n"
        for item in approved:
            content += f"### {item['title']}\n{item['text']}\n\n"
        content += "---\n"

    TEAM_NOTES_PATH.write_text(content, encoding="utf-8")

    # 구현 대기 파일 생성 → UserPromptSubmit 훅이 감지해 Claude에 주입
    if approved:
        pending = {
            "status": "pending",
            "topic": topic,
            "approved_at": datetime.datetime.now().isoformat(),
            "items": approved,
        }
        PENDING_IMPL_PATH.write_text(
            json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def build_pipeline_state() -> dict:
    """단일 파이프라인 state/pipeline.json 반환."""
    return load_json(STATE_PATH) or {}


def build_batch_state() -> dict:
    """병렬 파이프라인 상태 + tests/generated/ 파일 목록 반환."""
    parallel = load_json(PARALLEL_STATE_PATH) or {}
    generated_files = []
    if GENERATED_DIR.exists():
        for group_dir in sorted(GENERATED_DIR.iterdir()):
            if group_dir.is_dir() and not group_dir.name.startswith("."):
                for f in sorted(group_dir.glob("*.py")):
                    if f.name not in ("conftest.py", "__init__.py"):
                        generated_files.append({
                            "group": group_dir.name,
                            "file": f.name,
                            "path": str(f.relative_to(PROJECT_ROOT)),
                            "size": f.stat().st_size,
                        })
    return {"parallel_state": parallel, "generated_files": generated_files}


PAGES_JSON = PROJECT_ROOT / "config" / "pages.json"
TESTCASES_DIR = PROJECT_ROOT / "testcases"


def list_pages() -> dict:
    """config/pages.json 반환."""
    return load_json(PAGES_JSON) or {}


def list_testcase_groups() -> list:
    """testcases/ 하위 폴더별 케이스 파일 목록."""
    if not TESTCASES_DIR.exists():
        return []
    groups = []
    for d in sorted(TESTCASES_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        cases = sorted([f.name for f in d.glob("tc_*.md")])
        groups.append({"name": d.name, "cases": cases, "count": len(cases)})
    return groups


def _natural_sort_key(name: str) -> list:
    """숫자 부분을 정수로 변환해 자연 정렬 키 반환 (tc_9 < tc_10 < tc_11 보장)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", name)]


def list_generated_groups() -> list:
    """tests/generated/ 하위 그룹별 테스트 파일 목록 반환.
    testcases/ 의 .md 파일 기준으로 유효한 파일만 집계 (잔여 파일 제외).
    """
    if not GENERATED_DIR.exists():
        return []
    groups = []
    for d in sorted(GENERATED_DIR.iterdir(), key=lambda p: _natural_sort_key(p.name)):
        if not d.is_dir() or d.name.startswith((".", "_")):
            continue
        all_py = sorted([
            f.name for f in d.glob("tc_*.py")
        ], key=_natural_sort_key)
        # testcases/{group}/tc_*.md 기준으로 유효 파일 집합 산출 (번호 prefix로 매칭)
        tc_dir = TESTCASES_DIR / d.name
        if tc_dir.exists():
            import re as _re
            def _tc_num(name):
                m = _re.match(r'tc_(\d+)_', name)
                return m.group(1) if m else None
            valid_nums = {_tc_num(f.name) for f in tc_dir.glob("tc_*.md")} - {None}
            files = [f for f in all_py if _tc_num(f) in valid_nums]
            stale_count = len(all_py) - len(files)
        else:
            files = all_py
            stale_count = 0
        if files:
            entry = {
                "name": d.name,
                "file_count": len(files),
                "files": files,
            }
            if stale_count > 0:
                entry["stale_count"] = stale_count
            groups.append(entry)
    return groups


MAX_REPORTS = 200


def list_reports() -> list:
    """tests/reports/ 의 HTML 파일 목록 (최신순, 최대 MAX_REPORTS개)."""
    if not REPORTS_DIR.exists():
        return []
    reports = []
    for f in sorted(REPORTS_DIR.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)[:MAX_REPORTS]:
        reports.append({
            "name": f.name,
            "modified_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            "size": f.stat().st_size,
        })
    return reports


def build_dialogs() -> dict:
    """팀 토론 대화 payload 반환 (dialog.json은 팀 토론 전용)."""
    full_dialog = load_json(DIALOG_PATH) or {"sessions": []}
    discuss_state = load_json(DISCUSS_PATH) or {}

    # step=discussed 이고 conclusion_items 없으면 자동 파싱
    if (discuss_state.get("step") == "discussed"
            and discuss_state.get("conclusion")
            and not discuss_state.get("conclusion_items")):
        discuss_state["conclusion_items"] = parse_conclusion_items(discuss_state["conclusion"])
        DISCUSS_PATH.write_text(
            json.dumps(discuss_state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    all_sessions = full_dialog.get("sessions", [])
    team_sessions = [s for s in all_sessions if s.get("stage") == "team_discussion"]

    # discuss_state의 conclusion_items와 status를 topic이 일치하는 세션에 주입
    if discuss_state.get("topic"):
        for ts in team_sessions:
            if ts.get("topic") == discuss_state["topic"]:
                if discuss_state.get("conclusion_items"):
                    ts["conclusion_items"] = discuss_state["conclusion_items"]
                if discuss_state.get("step"):
                    ts["status"] = discuss_state["step"]
                break

    return {
        "team_sessions": team_sessions,
        "discuss_state": discuss_state,
    }


# ── Excel Import 유틸 ─────────────────────────────────────────
def _list_import_files() -> list:
    """import/ 폴더의 .xlsx 파일 목록."""
    if not IMPORT_DIR.exists():
        return []
    return sorted([f.name for f in IMPORT_DIR.glob("*.xlsx")])


def _detect_header_row(ws) -> int | None:
    """'Test\\nScenario ID' 패턴이 있는 헤더 행 번호 반환."""
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=20, values_only=False), 1):
        for cell in row:
            if cell.value and "Scenario ID" in str(cell.value):
                return i
    return None


def _list_excel_sheets(filepath: Path) -> list:
    """엑셀 파일의 시트별 테스트케이스 수 반환."""
    import openpyxl
    wb = openpyxl.load_workbook(str(filepath), data_only=True, read_only=True)
    sheets = []
    for name in wb.sheetnames:
        ws = wb[name]
        header_row = _detect_header_row(ws)
        if header_row is None:
            continue
        count = 0
        for row in ws.iter_rows(min_row=header_row + 2, values_only=False):
            cell_b = row[1].value if len(row) > 1 else None
            if cell_b and "_" in str(cell_b):
                count += 1
        if count > 0:
            sheets.append({"name": name, "count": count})
    wb.close()
    return sheets


def _parse_excel_sheet(wb, sheet_name: str) -> list:
    """엑셀 시트에서 테스트케이스 목록 추출."""
    ws = wb[sheet_name]
    header_row = _detect_header_row(ws)
    if header_row is None:
        return []

    last_main = ""
    last_sub = ""
    cases = []
    for row in ws.iter_rows(min_row=header_row + 2, values_only=False):
        tc_id = row[1].value if len(row) > 1 else None
        if not tc_id or "_" not in str(tc_id):
            continue
        main = str(row[2].value).strip() if len(row) > 2 and row[2].value else ""
        sub = str(row[3].value).strip() if len(row) > 3 and row[3].value else ""
        detail = str(row[4].value).strip() if len(row) > 4 and row[4].value else ""
        summary = str(row[5].value).strip() if len(row) > 5 and row[5].value else ""
        precond = str(row[6].value).strip() if len(row) > 6 and row[6].value else ""
        steps = str(row[7].value).strip() if len(row) > 7 and row[7].value else ""
        expected = str(row[8].value).strip() if len(row) > 8 and row[8].value else ""
        level = str(row[9].value).strip() if len(row) > 9 and row[9].value else ""
        if main:
            last_main = main
        else:
            main = last_main
        if sub:
            last_sub = sub
        else:
            sub = last_sub
        cases.append({
            "main": main, "sub": sub, "detail": detail,
            "summary": summary, "precondition": precond,
            "steps": steps, "expected": expected, "level": level,
        })
    return cases


def _level_to_priority(level: str) -> str:
    level = level.strip()
    if level in ("BAT", "Level 1"):
        return "high"
    elif level == "Level 2":
        return "medium"
    return "low"


def _to_slug(text: str) -> str:
    """TC Summary → 파일명 슬러그."""
    if not text:
        return "unnamed"
    text = text.replace("\n", " ").strip()
    text = re.sub(r'[/\\:*?"<>|.\[\]()>{},]', '', text)
    text = re.sub(r'\s+', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text[:60]


def _write_tc_files(cases: list, output_dir: Path) -> int:
    """케이스 목록을 tc_*.md 파일로 생성. 생성 건수 반환."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(cases):
        num = str(i + 1).zfill(3)
        slug = _to_slug(c["summary"])
        filepath = output_dir / f"tc_{num}_{slug}.md"
        priority = _level_to_priority(c.get("level", ""))
        tags = []
        if c["main"]:
            clean = re.sub(r'\(.*?\)', '', c["main"]).strip().replace('\n', '')
            if clean:
                tags.append(clean)
        if c["sub"]:
            tags.append(c["sub"].replace('\n', ''))
        if not tags:
            tags = ["general"]
        tags_str = ", ".join(tags)
        steps_lines = [s.strip() for s in c["steps"].split("\n")
                       if s.strip() and not s.strip().startswith("0.")]
        steps_text = "\n".join(steps_lines) if steps_lines else "1. (스텝 미기재)"
        exp_lines = []
        for e in c["expected"].split("\n"):
            e = e.strip()
            if e:
                if not e.startswith("-") and not e.startswith("*"):
                    e = f"- {e}"
                exp_lines.append(e)
        expected_text = "\n".join(exp_lines) if exp_lines else "- (기대결과 미기재)"
        pre_lines = [p.strip() for p in c["precondition"].split("\n") if p.strip()]
        precond_text = "\n".join(pre_lines) if pre_lines else "- 없음"
        title = c["summary"].replace("\n", " ").strip()
        content = (
            f"---\nid: tc_{num}\ndata_key: null\npriority: {priority}\n"
            f"tags: [{tags_str}]\ntype: structured\n---\n"
            f"# {title}\n\n## Precondition\n{precond_text}\n\n"
            f"## Steps\n{steps_text}\n\n## Expected\n{expected_text}\n"
        )
        filepath.write_text(content, encoding="utf-8")
    return len(cases)


def _read_body(handler) -> dict:
    """요청 바디를 JSON으로 파싱해 반환. 바디 없으면 빈 dict."""
    length = int(handler.headers.get("Content-Length", 0))
    return json.loads(handler.rfile.read(length).decode("utf-8")) if length else {}


class DashboardHandler(BaseHTTPRequestHandler):

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
        "/api/flaky_tests":      "_get_flaky_tests",
        "/api/generated_groups": "_get_generated_groups",
        "/api/reports":          "_get_reports",
        "/api/testcase":         "_get_testcase",
        "/api/import/files":     "_get_import_files",
        "/api/import/sheets":    "_get_import_sheets",
    }

    POST_ROUTES = {
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
        "/api/import/convert":     "_post_import_convert",
        "/api/heal_stats/reset":   "_post_heal_stats_reset",
        "/api/run_history/reset":  "_post_run_history_reset",
        "/api/discuss/reset":      "_post_discuss_reset",
    }

    # ── Dispatchers ───────────────────────────────────────────────
    def do_GET(self):
        path = self.path.split("?")[0]

        # index
        if path in ("/", "/index.html"):
            self._serve_file(HERE / "index.html", "text/html; charset=utf-8")
            return

        # exact-match routes
        if path in self.GET_ROUTES:
            getattr(self, self.GET_ROUTES[path])()
            return

        # prefix routes
        if path.startswith("/reports/"):
            self._get_report_file(path)
            return

        if path.startswith("/static/"):
            self._get_static_file(path)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
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
                self._serve_bytes(msg, "application/json; charset=utf-8")
            except Exception:
                pass

    # ── GET handlers ─────────────────────────────────────────────
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
        payload = {"pages": list_pages(), "groups": list_testcase_groups()}
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
        #           tests/generated/directcloud/tc_01_login_success_login_success.py::test_...
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
        # tc 번호 추출: tc_01_ → testcases/{group}/tc_01_*.md 검색
        m = _re.match(r"(tc_\d+)_", py_file)
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

    def _get_import_files(self):
        payload = {"ok": True, "files": _list_import_files()}
        self._serve_bytes(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _get_import_sheets(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        fname = qs.get("file", [""])[0]
        if not fname or ".." in fname:
            self._serve_bytes(
                b'{"ok":false,"error":"file parameter required"}',
                "application/json; charset=utf-8")
            return
        fpath = IMPORT_DIR / fname
        if not fpath.exists():
            self._serve_bytes(
                json.dumps({"ok": False, "error": f"{fname} not found"},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return
        try:
            sheets = _list_excel_sheets(fpath)
            self._serve_bytes(
                json.dumps({"ok": True, "sheets": sheets},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
        except Exception as e:
            self._serve_bytes(
                json.dumps({"ok": False, "error": str(e)},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")

    def _get_report_file(self, path: str):
        fname = path[len("/reports/"):]
        fpath = REPORTS_DIR / fname
        if fpath.exists() and fpath.suffix == ".html":
            content = fpath.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("X-XSS-Protection", "0")
            self.send_header("Content-Security-Policy",
                             "default-src 'self' https:; "
                             "script-src 'unsafe-inline'; "
                             "style-src 'unsafe-inline' https:; "
                             "font-src 'self' https: data:; "
                             "img-src 'self' data: blob:")
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def _get_static_file(self, path: str):
        rel = path[len("/static/"):]
        if ".." in rel:
            self.send_response(403)
            self.end_headers()
            return
        fpath = HERE / "static" / rel
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

    # ── POST handlers ─────────────────────────────────────────────
    def _post_reset(self):
        empty = {"pipeline_url": "", "started_at": "", "sessions": []}
        DIALOG_PATH.write_text(
            json.dumps(empty, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_discuss_start(self):
        import datetime
        body = _read_body(self)
        topic = body.get("topic", "").strip()
        if not topic:
            self._serve_bytes(b'{"ok":false,"error":"topic required"}',
                              "application/json; charset=utf-8")
            return

        history = []
        if DISCUSS_PATH.exists():
            try:
                prev = json.loads(DISCUSS_PATH.read_text(encoding="utf-8"))
                history = prev.get("history", [])
                if prev.get("step") in ("approved", "rejected", "discussed"):
                    history.append({k: v for k, v in prev.items() if k != "history"})
            except Exception:
                pass

        discuss = {
            "topic": topic, "step": "pending", "conclusion": "",
            "rejection_reason": "", "rejection_count": 0,
            "created_at": datetime.datetime.now().isoformat(),
            "history": history,
        }
        DISCUSS_PATH.write_text(
            json.dumps(discuss, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # Claude Code UserPromptSubmit 훅(check_pending_discuss.py)이
        # 다음 프롬프트 제출 시 자동으로 토론 시작을 Claude에게 주입한다.
        self._serve_bytes(b'{"ok":true}',
                          "application/json; charset=utf-8")

    def _post_discuss_vote_item(self):
        body = _read_body(self)
        item_id = int(body.get("item_id", -1))
        vote    = body.get("vote", "")  # "approve" | "reject"

        if not DISCUSS_PATH.exists():
            self._serve_bytes(
                json.dumps({"ok": False, "error": "state/discuss.json 없음"}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return

        discuss = json.loads(DISCUSS_PATH.read_text(encoding="utf-8"))
        items = discuss.get("conclusion_items", [])
        for item in items:
            if item["id"] == item_id:
                item["status"] = "approved" if vote == "approve" else "rejected"
                break
        discuss["conclusion_items"] = items

        all_voted = bool(items) and all(i["status"] != "pending" for i in items)
        if all_voted:
            finalize_team_notes(discuss)
            discuss["step"] = "approved"

        DISCUSS_PATH.write_text(
            json.dumps(discuss, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._serve_bytes(
            json.dumps({"ok": True, "all_voted": all_voted}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _post_discuss_reject(self):
        body = _read_body(self)
        reason = body.get("reason", "").strip()
        if not DISCUSS_PATH.exists():
            self._serve_bytes(
                json.dumps({"ok": False, "error": "state/discuss.json 없음"}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return
        discuss = json.loads(DISCUSS_PATH.read_text(encoding="utf-8"))
        discuss["step"] = "rejected"
        discuss["rejection_reason"] = reason
        discuss["rejection_count"] = discuss.get("rejection_count", 0) + 1
        DISCUSS_PATH.write_text(
            json.dumps(discuss, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_run_qa(self):
        import subprocess as sp
        body = _read_body(self)
        url = body.get("url", "").strip()
        cases_dir = body.get("cases_dir", "").strip()  # e.g. "login"
        # 입력 검증: URL은 http(s)로 시작, cases_dir은 영숫자/언더스코어/하이픈만
        if url and not url.startswith(("http://", "https://")):
            self._serve_bytes(
                b'{"ok":false,"error":"url must start with http:// or https://"}',
                "application/json; charset=utf-8")
            return
        if cases_dir and not re.match(r'^[\w\-]+$', cases_dir):
            self._serve_bytes(
                b'{"ok":false,"error":"invalid cases_dir format"}',
                "application/json; charset=utf-8")
            return
        if not url or not cases_dir:
            self._serve_bytes(
                b'{"ok":false,"error":"url and cases_dir required"}',
                "application/json; charset=utf-8")
            return
        cases_path = TESTCASES_DIR / cases_dir
        if not cases_path.exists():
            self._serve_bytes(
                json.dumps({"ok": False, "error": f"testcases/{cases_dir} not found"}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return
        log_path = LOGS_DIR / "run_qa.txt"
        script = PROJECT_ROOT / "run_qa.py"
        log_file = open(log_path, "w", encoding="utf-8")
        proc = sp.Popen(
            [PYTHON_EXE, "-u", str(script),
             "--url", url, "--cases", str(cases_path)],
            cwd=str(PROJECT_ROOT),
            stdout=log_file, stderr=sp.STDOUT,
        )
        # 자식 프로세스가 fd를 상속했으므로 부모에서 닫아도 안전
        log_file.close()
        print(f"[Dashboard] run_qa.py 실행 (PID: {proc.pid}, URL: {url}, cases: {cases_dir})")
        self._serve_bytes(
            json.dumps({"ok": True, "pid": proc.pid, "log": str(log_path)}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _post_run_qa_parallel(self):
        import subprocess as sp
        log_path = LOGS_DIR / "run_parallel.txt"
        script = PROJECT_ROOT / "run_qa_parallel.py"
        log_file = open(log_path, "w", encoding="utf-8")
        proc = sp.Popen(
            [PYTHON_EXE, "-u", str(script)],
            cwd=str(PROJECT_ROOT),
            stdout=log_file, stderr=sp.STDOUT,
        )
        log_file.close()
        print(f"[Dashboard] run_qa_parallel.py 실행 (PID: {proc.pid})")
        self._serve_bytes(
            json.dumps({"ok": True, "pid": proc.pid, "log": str(log_path)}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _post_run_log(self):
        body = _read_body(self)
        log_name = body.get("log", "run_qa.txt")
        # 보안: 상위 디렉토리 접근 방지
        if ".." in log_name or "/" in log_name:
            self._serve_bytes(b'{"ok":false,"log":""}', "application/json; charset=utf-8")
            return
        log_path = LOGS_DIR / log_name
        if log_path.exists():
            content = log_path.read_text(encoding="utf-8", errors="replace")
            self._serve_bytes(
                json.dumps({"ok": True, "log": content}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8"
            )
        else:
            self._serve_bytes(b'{"ok":false,"log":""}', "application/json; charset=utf-8")

    def _post_reset_all(self):
        # dialog
        empty = {"pipeline_url": "", "started_at": "", "sessions": []}
        DIALOG_PATH.write_text(json.dumps(empty, ensure_ascii=False, indent=2), encoding="utf-8")
        # pipeline
        init_state = {
            "url": "", "test_cases": [], "step": "init",
            "dom_info": {}, "plan": [],
            "generated_file_path": "tests/generated/test_generated.py",
            "lint_result": {}, "review_summary": "",
            "approval_status": "", "rejection_reason": "",
            "rejection_count": 0, "execution_result": {},
            "heal_count": 0, "heal_context": {}
        }
        STATE_PATH.write_text(json.dumps(init_state, ensure_ascii=False, indent=2), encoding="utf-8")
        # parallel
        PARALLEL_STATE_PATH.write_text(
            json.dumps({"status": "", "total_count": 0, "targets": []}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        heal_ctx = PROJECT_ROOT / "state" / "heal_context.json"
        if heal_ctx.exists():
            heal_ctx.unlink()
        # quick
        if QUICK_STATE_PATH.exists():
            QUICK_STATE_PATH.unlink()
        # heal stats
        HEAL_STATS_PATH.write_text(
            json.dumps({"version": 1, "patterns": {}}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # run history
        RUN_HISTORY_PATH.write_text("[]", encoding="utf-8")
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_pipeline_reset(self):
        init_state = {
            "url": "", "test_cases": [], "step": "init",
            "dom_info": {}, "plan": [],
            "generated_file_path": "tests/generated/test_generated.py",
            "lint_result": {}, "review_summary": "",
            "approval_status": "", "rejection_reason": "",
            "rejection_count": 0, "execution_result": {},
            "heal_count": 0, "heal_context": {}
        }
        STATE_PATH.write_text(
            json.dumps(init_state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_parallel_reset(self):
        init_state = {"status": "", "total_count": 0, "targets": []}
        PARALLEL_STATE_PATH.write_text(
            json.dumps(init_state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # heal_context도 정리
        heal_ctx = PROJECT_ROOT / "state" / "heal_context.json"
        if heal_ctx.exists():
            heal_ctx.unlink()
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_quick_reset(self):
        import subprocess as sp
        body = _read_body(self)
        pid = body.get("pid") if body else None
        if pid:
            try:
                if sys.platform == "win32":
                    sp.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                           capture_output=True, timeout=5)
                else:
                    import os as _os
                    _os.kill(int(pid), 15)
            except Exception:
                pass
        if QUICK_STATE_PATH.exists():
            QUICK_STATE_PATH.unlink()
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_heal_stats_reset(self):
        init = {"version": 1, "patterns": {}}
        HEAL_STATS_PATH.write_text(
            json.dumps(init, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_run_history_reset(self):
        RUN_HISTORY_PATH.write_text("[]", encoding="utf-8")
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_discuss_reset(self):
        # discuss.json 초기화 (topic/step/conclusion 등 모든 상태 제거)
        DISCUSS_PATH.write_text(
            json.dumps({}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # dialog.json의 team_discussion 세션도 제거
        dialog = load_json(DIALOG_PATH) or {"sessions": []}
        dialog["sessions"] = [
            s for s in dialog.get("sessions", [])
            if s.get("stage") != "team_discussion"
        ]
        DIALOG_PATH.write_text(
            json.dumps(dialog, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._serve_bytes(b'{"ok":true}', "application/json; charset=utf-8")

    def _post_run_merge(self):
        import subprocess as sp
        merge_script = PROJECT_ROOT / "parallel" / "99_merge.py"
        if not merge_script.exists():
            self._serve_bytes(b'{"ok":false,"error":"99_merge.py not found"}',
                              "application/json; charset=utf-8")
            return
        # 로그 파일로 출력 저장
        log_path = LOGS_DIR / "merge.txt"
        log_file = open(log_path, "w", encoding="utf-8")
        proc = sp.Popen(
            [PYTHON_EXE, "-u", str(merge_script)],
            cwd=str(PROJECT_ROOT),
            stdout=log_file, stderr=sp.STDOUT,
        )
        log_file.close()
        print(f"[Dashboard] 99_merge.py 실행 (PID: {proc.pid}, 로그: {log_path})")
        self._serve_bytes(
            json.dumps({"ok": True, "message": "99_merge.py started", "pid": proc.pid,
                         "log": str(log_path)}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _post_merge_log(self):
        log_path = LOGS_DIR / "merge.txt"
        if log_path.exists():
            content = log_path.read_text(encoding="utf-8", errors="replace")
            self._serve_bytes(
                json.dumps({"ok": True, "log": content}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8"
            )
        else:
            self._serve_bytes(b'{"ok":false,"log":""}',
                              "application/json; charset=utf-8")

    def _post_run_quick(self):
        import subprocess as sp
        body = _read_body(self)
        groups = body.get("groups", [])
        if not groups:
            self._serve_bytes(
                b'{"ok":false,"error":"groups required"}',
                "application/json; charset=utf-8")
            return
        # 그룹명 형식 검증 (경로 탈출 방지)
        invalid = [g for g in groups if not re.match(r'^[\w\-]+$', g)]
        if invalid:
            self._serve_bytes(
                json.dumps({"ok": False, "error": f"잘못된 그룹명: {', '.join(invalid)}"},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return
        # 폴더 존재 검증
        missing = [g for g in groups if not (GENERATED_DIR / g).is_dir()]
        if missing:
            msg = json.dumps(
                {"ok": False, "error": f"존재하지 않는 폴더: {', '.join(missing)}"},
                ensure_ascii=False).encode("utf-8")
            self._serve_bytes(msg, "application/json; charset=utf-8")
            return
        log_path = LOGS_DIR / "quick_run.txt"
        merge_script = PROJECT_ROOT / "parallel" / "99_merge.py"
        log_file = open(log_path, "w", encoding="utf-8")
        no_heal = body.get("no_heal", False)
        cmd = [PYTHON_EXE, "-u", str(merge_script), "--quick", "--group"] + groups
        if no_heal:
            cmd.append("--no-heal")
        proc = sp.Popen(
            cmd, cwd=str(PROJECT_ROOT),
            stdout=log_file, stderr=sp.STDOUT,
        )
        log_file.close()
        print(f"[Dashboard] 빠른 실행 (PID: {proc.pid}, groups: {groups})")
        self._serve_bytes(
            json.dumps({"ok": True, "pid": proc.pid,
                         "log": str(log_path)}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8"
        )

    def _post_import_convert(self):
        import openpyxl
        body = _read_body(self)
        fname = body.get("file", "").strip()
        sheet_names = body.get("sheets", [])
        if not fname or not sheet_names:
            self._serve_bytes(
                b'{"ok":false,"error":"file and sheets required"}',
                "application/json; charset=utf-8")
            return
        fpath = IMPORT_DIR / fname
        if not fpath.exists():
            self._serve_bytes(
                json.dumps({"ok": False, "error": f"{fname} not found"},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return
        try:
            wb = openpyxl.load_workbook(str(fpath), data_only=True)
            results = []
            for sn in sheet_names:
                if sn not in wb.sheetnames:
                    results.append({"sheet": sn, "count": 0, "error": "시트 없음"})
                    continue
                cases = _parse_excel_sheet(wb, sn)
                folder_name = re.sub(r'\s+', '_', sn.strip().lower())
                out_dir = TESTCASES_DIR / folder_name
                # 기존 파일 정리
                if out_dir.exists():
                    for old in out_dir.glob("tc_*.md"):
                        old.unlink()
                count = _write_tc_files(cases, out_dir)
                results.append({"sheet": sn, "count": count,
                                "folder": f"testcases/{folder_name}/"})
            wb.close()
            self._serve_bytes(
                json.dumps({"ok": True, "results": results},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
        except Exception as e:
            self._serve_bytes(
                json.dumps({"ok": False, "error": str(e)},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")

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

    def _serve_bytes(self, content: bytes, content_type: str):
        self.send_response(200)
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


def main():
    server = ReusableHTTPServer(("127.0.0.1", PORT), DashboardHandler)
    url = f"http://localhost:{PORT}"
    print(f"[Dashboard] 서버 시작: {url}")
    print(f"[Dashboard] 종료: Ctrl+C")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Dashboard] 서버 종료")


if __name__ == "__main__":
    main()
