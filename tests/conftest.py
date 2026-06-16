import json
import pytest
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

# 테스트별 콘솔/네트워크 로그를 저장하는 딕셔너리 (test_name → logs)
_console_logs: dict = {}
_network_failures: dict = {}
_test_outcomes: dict = {}   # test_name -> pytest outcome string ("passed"/"failed"/"skipped")
_video_paths: dict = {}     # test_name -> renamed video file path (실패 TC만)


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
    test_file = Path(str(request.node.fspath))
    group = test_file.parent.name if test_file.parent.name != "generated" else "default"

    _console_logs[test_name] = []
    _network_failures[test_name] = []

    video_dir = Path("tests/videos")
    video_dir.mkdir(parents=True, exist_ok=True)

    context = browser_instance.new_context(
        record_video_dir=str(video_dir),
        record_video_size={"width": 1280, "height": 720},
    )
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()

    page.on("dialog", lambda dialog: dialog.accept())
    page.on("console", lambda msg: _console_logs[test_name].append({
        "type": msg.type,
        "text": msg.text,
    }) if msg.type in ("error", "warning") and test_name in _console_logs else None)
    page.on("requestfailed", lambda req: _network_failures[test_name].append({
        "url": req.url,
        "method": req.method,
        "failure": req.failure,
    }) if test_name in _network_failures else None)
    page.on("response", lambda res: _network_failures[test_name].append({
        "url": res.url,
        "method": res.request.method,
        "status": res.status,
        "failure": f"HTTP {res.status}",
    }) if res.status >= 400 and test_name in _network_failures else None)

    yield page

    # Teardown: page.video.path() 는 context.close() 전에 호출해야 함
    video_path_raw = None
    try:
        if page.video:
            video_path_raw = page.video.path()
    except Exception:
        pass

    context.close()  # 이 시점에 video 파일이 디스크에 확정됨

    # 실패 여부에 따라 video 보존 또는 삭제
    outcome = _test_outcomes.pop(test_name, "passed")
    if video_path_raw and Path(video_path_raw).exists():
        if outcome == "passed":
            Path(video_path_raw).unlink(missing_ok=True)
        else:
            dest = video_dir / f"{group}__{test_name}.mp4"
            try:
                Path(video_path_raw).rename(dest)
                _video_paths[test_name] = str(dest)
            except Exception:
                _video_paths[test_name] = video_path_raw

    # meta.json에 video_path 추가 (실패 TC의 meta.json은 이미 makereport에서 작성됨)
    if outcome != "passed" and test_name in _video_paths:
        shot_dir = Path("tests/screenshots")
        meta_path = shot_dir / f"{group}__{test_name}.meta.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                meta["video_path"] = _video_paths.get(test_name, "")
                meta_path.write_text(
                    json.dumps(meta, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception:
                pass

    # 메모리 정리
    _video_paths.pop(test_name, None)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        # fixture teardown에서 video 처리에 사용
        _test_outcomes[item.name] = report.outcome

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
                        "video_path": "",  # fixture teardown에서 채워짐
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
