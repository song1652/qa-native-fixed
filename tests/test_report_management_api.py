from __future__ import annotations

import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

import pytest

from tests.import_studio_test_support import (
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
    dash_state = __import__("dash_state")
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    vanished = reports_dir / "vanished.html"
    vanished.write_text("vanished", encoding="utf-8")
    monkeypatch.setattr(serve, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(dash_state, "REPORTS_DIR", reports_dir)
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
