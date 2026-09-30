from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

import pytest

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
from tests.unit.tc_library.tc_fixtures import build_template_workbook
from tests.unit.tc_library.test_tc_library_api import _post_bytes

S = quote("야핏무브")


@pytest.fixture
def api(tmp_path: Path):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    (project / "config").mkdir()
    (project / "config" / "pages.json").write_text(json.dumps({"yafit_benefit": "https://m.yafit.example/b"}), encoding="utf-8")
    with dashboard_server(project) as base_url:          # PAGES_JSON도 project/config/pages.json으로 격리된다
        _, preview = _post_bytes(base_url, "/api/tc-library/import/preview?filename=a.xlsx",
                                 build_template_workbook(tmp_path / "src.xlsx").read_bytes())
        request_json(base_url, "POST", "/api/tc-library/import", {
            "preview_id": preview["preview_id"], "suite": "야핏무브", "sheets": ["혜택"], "prefixes": {"혜택": "BEN"}})
        for case_id in ("BEN_0001", "BEN_0002"):
            request_json(base_url, "PATCH", f"/api/tc-library/{S}/cases/{case_id}", {"rev": 1, "priority": "P0"})
        yield base_url, project


def test_md_export_flow(api):
    base_url, project = api
    body = request_json(base_url, "GET", f"/api/tc-library/{S}/export/md/eligibility")[1]
    assert [f["count"] for f in body["funnel"]] == [5, 5, 5, 0] and body["pages"] == ["yafit_benefit"]
    status, body = request_json(base_url, "PUT", f"/api/tc-library/{S}/md-groups",
                                {"path": ["혜택", "혜택 탭"], "group": "yafit_benefit", "code": "YFB"})
    assert status == 200 and body["groups"][0]["code"] == "YFB"

    status, run = request_json(base_url, "POST", f"/api/tc-library/{S}/export/md")
    assert status == 200 and run["summary"]["added"] == 5
    assert run["rows"][0]["file"].startswith("yafit_benefit/tc_YFB_01_")
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/md-exports/{run['run_id']}/commit", {"skip": []})
    assert (status, body["created"]) == (200, 5)
    assert len(list((project / "testcases" / "yafit_benefit").glob("tc_YFB_*.md"))) == 5
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/md-exports/{run['run_id']}/rollback")
    assert status == 200 and not list((project / "testcases" / "yafit_benefit").glob("tc_YFB_*.md"))
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/md-exports/{run['run_id']}/commit", {"skip": []})
    assert (status, body["code"]) == (409, "INVALID_RUN_STATE")
    assert request_json(base_url, "PUT", f"/api/tc-library/{S}/md-groups",
                        {"path": ["혜택", "혜택 탭"], "group": "nope", "code": "YFB"})[1]["code"] == "GROUP_NOT_IN_PAGES"
