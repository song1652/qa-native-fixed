import json
import pytest
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

# 테스트별 콘솔/네트워크 로그를 저장하는 딕셔너리 (test_name → logs)
_console_logs: dict = {}
_network_failures: dict = {}

@pytest.fixture(scope="session")
def browser_instance():
    import os
    headless = os.environ.get("HEADED", "0") != "1"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        yield browser
        browser.close()


@pytest.fixture
def page(browser_instance, request):
    test_name = request.node.name
    _console_logs[test_name] = []
    _network_failures[test_name] = []

    context = browser_instance.new_context()
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()

    page.on("dialog", lambda dialog: dialog.accept())
    page.on("console", lambda msg: _console_logs[test_name].append({
        "type": msg.type,
        "text": msg.text,
    }) if msg.type in ("error", "warning") else None)
    page.on("requestfailed", lambda req: _network_failures[test_name].append({
        "url": req.url,
        "method": req.method,
        "failure": req.failure,
    }))
    page.on("response", lambda res: _network_failures[test_name].append({
        "url": res.url,
        "method": res.request.method,
        "status": res.status,
        "failure": f"HTTP {res.status}",
    }) if res.status >= 400 else None)

    yield page
    context.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        page = item.funcargs.get("page")
        if page:
            test_file = Path(item.fspath)
            group = test_file.parent.name if test_file.parent.name != "generated" else "default"

            if report.failed:
                shot_dir = Path("tests/screenshots")
                shot_dir.mkdir(parents=True, exist_ok=True)
                path = shot_dir / f"{group}__{item.name}.png"
                trace_dir = Path("tests/traces")
                trace_dir.mkdir(parents=True, exist_ok=True)
                trace_path = trace_dir / f"{group}__{item.name}.zip"
                try:
                    page.screenshot(path=str(path))
                    page.context.tracing.stop(path=str(trace_path))
                    meta = {
                        "test_name": item.name,
                        "group": group,
                        "url": page.url,
                        "timestamp": datetime.now().isoformat(),
                        "screenshot_path": str(path),
                        "trace_path": str(trace_path),
                        "console_errors": _console_logs.get(item.name, []),
                        "network_failures": _network_failures.get(item.name, []),
                    }
                    meta_path = shot_dir / f"{group}__{item.name}.meta.json"
                    meta_path.write_text(
                        json.dumps(meta, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    print(f"\n스크린샷 저장: {path}")
                    print(f"Trace 저장: {trace_path}  →  npx playwright show-trace {trace_path}")
                except Exception:
                    pass
            else:
                try:
                    page.context.tracing.stop()
                except Exception:
                    pass
            # 메모리 정리
            _console_logs.pop(item.name, None)
            _network_failures.pop(item.name, None)
