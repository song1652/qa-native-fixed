from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import threading
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import openpyxl


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
DASHBOARD_DIR = REPO_ROOT / "agents" / "dashboard"
FIXTURE_SPEC = REPO_ROOT / "tests" / "fixtures" / "import_studio" / "workbooks.json"


def materialize_workbooks(import_dir: Path) -> dict[str, Path]:
    """Create deterministic Excel fixtures outside the repository data folders."""
    spec = json.loads(FIXTURE_SPEC.read_text(encoding="utf-8"))
    import_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for filename, sheets in spec.items():
        workbook = openpyxl.Workbook()
        workbook.remove(workbook.active)
        for sheet_name, rows in sheets.items():
            worksheet = workbook.create_sheet(sheet_name)
            for row in rows:
                worksheet.append(row)
        path = import_dir / filename
        workbook.save(path)
        workbook.close()
        paths[filename] = path
    return paths


def tree_digest(root: Path) -> str:
    """Hash a file tree by relative path and bytes, ignoring filesystem metadata."""
    digest = hashlib.sha256()
    if not root.exists():
        return digest.hexdigest()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def workbook_id(filename: str) -> str:
    return hashlib.sha256(filename.encode("utf-8")).hexdigest()[:8]


def load_dashboard_module():
    for module_path in (str(SCRIPTS_DIR), str(DASHBOARD_DIR)):
        if module_path not in sys.path:
            sys.path.insert(0, module_path)
    module_name = "serve_import_studio_tests"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, DASHBOARD_DIR / "serve.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def configure_isolated_project(serve: Any, project_root: Path) -> None:
    """Point every Import Studio write boundary at a temporary project tree."""
    import _paths

    paths = {
        "PROJECT_ROOT": project_root,
        "IMPORT_DIR": project_root / "import",
        "TESTCASES_DIR": project_root / "testcases",
        "GENERATED_DIR": project_root / "tests" / "generated",
        "REPORTS_DIR": project_root / "tests" / "reports",
        "SCREENSHOTS_DIR": project_root / "tests" / "screenshots",
        "VIDEOS_DIR": project_root / "tests" / "videos",
        "IMPORT_SESSIONS_DIR": project_root / "state" / "import_sessions",
        "IMPORT_SNAPSHOTS_DIR": project_root / "state" / "import_snapshots",
        "IMPORT_PROFILES_PATH": project_root / "state" / "import_profiles.json",
    }
    for name, value in paths.items():
        if hasattr(serve, name):
            setattr(serve, name, value)
        if hasattr(_paths, name):
            setattr(_paths, name, value)


@contextmanager
def dashboard_server(project_root: Path) -> Iterator[str]:
    serve = load_dashboard_module()
    configure_isolated_project(serve, project_root)
    server = serve.ReusableHTTPServer(("127.0.0.1", 0), serve.DashboardHandler)
    port = server.server_address[1]
    serve.ALLOWED_HOSTS = {f"127.0.0.1:{port}", f"localhost:{port}"}
    serve.ALLOWED_ORIGIN = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request_json(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))
