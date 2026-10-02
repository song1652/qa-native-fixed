from __future__ import annotations

import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

import pytest

from tests.unit.import_studio.import_studio_test_support import (
    dashboard_server,
    load_dashboard_module,
    request_json,
)


@pytest.fixture
def report_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    project = tmp_path / "project"
    reports_dir = project / "tests" / "reports"
    reports_dir.mkdir(parents=True)
    # The dashboard is split into route modules; each imports path constants
    # once, so keep every report boundary pointed at this isolated tree.
    with dashboard_server(project) as base_url:
        serve = load_dashboard_module()
        for module_name in ("_paths", "dash_state", "routes_get"):
            module = __import__(module_name)
            if hasattr(module, "REPORTS_DIR"):
                monkeypatch.setattr(module, "REPORTS_DIR", reports_dir)
        monkeypatch.setattr(serve, "REPORTS_DIR", reports_dir)
        yield base_url, reports_dir


def test_delete_reports_returns_deleted_and_missing(report_api):
    base_url, reports_dir = report_api
    (reports_dir / "first.html").write_text("first", encoding="utf-8")
    (reports_dir / "second.html").write_text("second", encoding="utf-8")

    status, body = request_json(
        base_url,
        "POST",
        "/api/reports/delete",
        {"names": ["first.html", "absent.html", "second.html", "first.html"]},
    )

    assert status == 200
    assert body == {
        "ok": True,
        "deleted": ["first.html", "second.html"],
        "missing": ["absent.html"],
        "failed": [],
    }
    assert not (reports_dir / "first.html").exists()
    assert not (reports_dir / "second.html").exists()


def test_delete_reports_returns_per_file_permission_failure(
    report_api, monkeypatch: pytest.MonkeyPatch
):
    base_url, reports_dir = report_api
    deletable = reports_dir / "deletable.html"
    locked = reports_dir / "locked.html"
    deletable.write_text("delete", encoding="utf-8")
    locked.write_text("keep", encoding="utf-8")
    original_unlink = Path.unlink

    def unlink_with_permission_error(path: Path, *args, **kwargs):
        if path == locked:
            raise PermissionError("permission denied")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", unlink_with_permission_error)

    status, body = request_json(
        base_url,
        "POST",
        "/api/reports/delete",
        {"names": ["deletable.html", "locked.html", "missing.html"]},
    )

    assert status == 200
    assert body == {
        "ok": False,
        "deleted": ["deletable.html"],
        "missing": ["missing.html"],
        "failed": [{"name": "locked.html", "error": "permission denied"}],
    }
    assert not deletable.exists()
    assert locked.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize(
    "names",
    [
        [],
        "report.html",
        ["../report.html"],
        ["sub/report.html"],
        ["report.txt"],
        ["report.HTML"],
        ["report\u0000.html"],
        [123],
    ],
)
def test_delete_reports_rejects_invalid_names_without_mutation(
    report_api, names
):
    base_url, reports_dir = report_api
    report = reports_dir / "keep.html"
    report.write_text("keep", encoding="utf-8")
    payload_names = (
        ["keep.html", *names]
        if isinstance(names, list) and names
        else names
    )

    status, body = request_json(
        base_url,
        "POST",
        "/api/reports/delete",
        {"names": payload_names},
    )

    assert status == 400
    assert body["ok"] is False
    assert body["code"] == "INVALID_REPORT_NAMES"
    assert report.read_text(encoding="utf-8") == "keep"


def test_delete_reports_rejects_symlink_without_touching_target(
    report_api, tmp_path: Path
):
    base_url, reports_dir = report_api
    target = tmp_path / "outside.html"
    target.write_text("outside", encoding="utf-8")
    link = reports_dir / "linked.html"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are unavailable on this platform")

    status, body = request_json(
        base_url,
        "POST",
        "/api/reports/delete",
        {"names": ["linked.html"]},
    )

    assert status == 400
    assert body["code"] == "INVALID_REPORT_NAMES"
    assert link.is_symlink()
    assert target.read_text(encoding="utf-8") == "outside"


def test_encoded_report_name_is_served(report_api):
    base_url, reports_dir = report_api
    name = "특수 '인용\" <태그>&.html"
    content = "<html><body>encoded report</body></html>"
    (reports_dir / name).write_text(content, encoding="utf-8")

    encoded_url = f"{base_url}/reports/{quote(name, safe='')}"
    with urlopen(encoded_url, timeout=10) as response:
        assert response.status == 200
        assert response.read().decode("utf-8") == content


@pytest.mark.parametrize(
    "encoded_name",
    [
        "%2e%2e%2foutside.html",
        "%2e%2e%5coutside.html",
        "%2fetc%2fpasswd.html",
    ],
)
def test_encoded_report_traversal_is_rejected(report_api, encoded_name):
    base_url, _ = report_api

    with pytest.raises(HTTPError) as error:
        urlopen(f"{base_url}/reports/{encoded_name}", timeout=10)

    assert error.value.code == 403


def test_report_list_excludes_symlinks_and_html_directories(
    report_api, tmp_path: Path
):
    base_url, reports_dir = report_api
    (reports_dir / "regular.html").write_text("regular", encoding="utf-8")
    (reports_dir / "directory.html").mkdir()
    target = tmp_path / "outside.html"
    target.write_text("outside", encoding="utf-8")
    link = reports_dir / "linked.html"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are unavailable on this platform")

    status, reports = request_json(base_url, "GET", "/api/reports")

    assert status == 200
    assert [report["name"] for report in reports] == ["regular.html"]
    with pytest.raises(HTTPError) as error:
        urlopen(f"{base_url}/reports/linked.html", timeout=10)
    assert error.value.code == 404


def test_report_list_ignores_file_removed_during_stat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    serve = load_dashboard_module()
    _paths = __import__("_paths")
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    vanished = reports_dir / "vanished.html"
    vanished.write_text("vanished", encoding="utf-8")
    monkeypatch.setattr(serve, "REPORTS_DIR", reports_dir)
    # dash_state.py는 이제 REPORTS_DIR을 자체 바인딩하지 않고 _paths.REPORTS_DIR을
    # 동적으로 참조하므로(테스트 격리를 위한 단일 소스), 여기만 패치하면 된다.
    monkeypatch.setattr(_paths, "REPORTS_DIR", reports_dir)
    original_stat = Path.stat

    def stat_with_race(path: Path, *args, **kwargs):
        if path == vanished:
            raise FileNotFoundError(path)
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", stat_with_race)

    assert serve.list_reports() == []


def test_report_list_returns_more_than_two_hundred_items(report_api):
    base_url, reports_dir = report_api
    oldest = reports_dir / "oldest.html"
    oldest.write_text("oldest", encoding="utf-8")
    os.utime(oldest, (1, 1))
    for index in range(205):
        (reports_dir / f"report-{index:03}.html").write_text(
            str(index), encoding="utf-8"
        )

    status, reports = request_json(base_url, "GET", "/api/reports")

    assert status == 200
    assert len(reports) == 206
    assert reports[-1]["name"] == "oldest.html"


LEGACY_REPORT = '''<!DOCTYPE html><html lang="ko"><head><title>QA Report</title>
<style>:root {--bg:#0d1117;} body{background:var(--bg);}</style></head><body>
<div class="layout"><aside class="sidebar"><li id="nav_all" data-nav="all">All (2)</li></aside>
<div class="main"><div class="topbar"><h1>Test Results</h1><div class="overall-badge fail">1 FAILED</div></div>
<div class="stat-lbl">Pass Rate</div><section class="group-card" id="group_demo">
<div class="group-sub">1 / 2 passed</div><div class="group-title">DEMO</div>
<button class="fbtn" data-filter="demo" data-filter-val="all">All (2)</button>
<div class="case-item fail" data-status="fail" data-toggle="demo_1"><span class="case-title">ALL PASS 표기를 검증하는 원본 제목</span>
<span class="case-status-txt fail">FAIL</span><div id="detail_demo_1"><span class="detail-label">Steps</span>
<span class="detail-val">원본 입력: Test Results / PASS / FAIL</span><img src="/screenshots/failure.png" class="screenshot-thumb"></div></div>
</section></div></div><script>var _gState = {};
function toggleGroup(label) {return label;}</script></body></html>'''


def test_legacy_report_uses_current_theme_without_changing_saved_results(report_api):
    base_url, reports_dir = report_api
    original = LEGACY_REPORT.encode('utf-8')
    path = reports_dir / 'legacy.html'
    path.write_bytes(original)
    with urlopen(f'{base_url}/reports/legacy.html', timeout=10) as response:
        content = response.read()
        assert int(response.headers['Content-Length']) == len(content)
    html = content.decode('utf-8')
    assert '--bg:#F5F6F8' in html
    assert '#0d1117' not in html
    assert '<h1>테스트 리포트</h1>' in html
    assert '1건 실패' in html and '>실패</span>' in html
    assert '>전체 (2)</button>' in html and '>통과율</div>' in html
    assert 'ALL PASS 표기를 검증하는 원본 제목' in html
    assert '원본 입력: Test Results / PASS / FAIL' in html
    assert 'data-status="fail" data-toggle="demo_1"' in html
    assert 'id="detail_demo_1"' in html and '/screenshots/failure.png' in html
    assert "startsWith('전체')" in html
    assert path.read_bytes() == original


def test_missing_report_uses_light_readable_empty_state(report_api):
    base_url, _ = report_api
    with pytest.raises(HTTPError) as error:
        urlopen(f'{base_url}/reports/missing.html', timeout=10)
    assert error.value.code == 404
    html = error.value.read().decode('utf-8')
    assert '리포트가 삭제되었습니다' in html
    assert '#F5F6F8' in html and '#111827' in html
    assert '#08071b' not in html and '🗑' not in html
