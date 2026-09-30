from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from urllib.parse import quote

import pytest

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
from tests.unit.tc_library.connector_fixtures import (
    CLOUD, FIGMA_URL, PAGE_ID, STORAGE_V15, setup_confluence, setup_figma,
)
from tests.unit.tc_library.tc_fixtures import build_template_workbook
from tests.unit.tc_library.test_tc_library_api import _post_bytes

S = quote("야핏무브")


@pytest.fixture
def api(tmp_path: Path, fake_web):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        xlsx = build_template_workbook(tmp_path / "src.xlsx").read_bytes()
        _, preview = _post_bytes(base_url, "/api/tc-library/import/preview?filename=a.xlsx", xlsx)
        request_json(base_url, "POST", "/api/tc-library/import", {
            "preview_id": preview["preview_id"], "suite": "야핏무브", "sheets": ["혜택"], "prefixes": {"혜택": "BEN"}})
        bundle = request_json(base_url, "POST", "/api/tc-library/sources")[1]["bundle_id"]
        yield base_url, bundle, fake_web


def test_credentials_never_return_tokens(api):
    base_url, _, _ = api
    status, body = request_json(base_url, "PUT", "/api/tc-library/credentials/confluence",
                                {"base_url": CLOUD, "email": "qa.lead@yafit.com", "token": "secret-token"})
    assert status == 200 and body["confluence"]["configured"] is True
    got = request_json(base_url, "GET", "/api/tc-library/credentials")[1]
    assert "secret-token" not in json.dumps(got) and got["confluence"]["email_masked"] == "qa****@yafit.com"
    assert request_json(base_url, "PUT", "/api/tc-library/credentials/slack", {})[0] == 404


def test_remote_sources_and_assets(api):
    base_url, bundle, web = api
    setup_confluence(web)
    setup_figma(web)
    web.add("https://docs.example.com/prd", "<h1>PRD</h1><p>본문</p>", headers={"Content-Type": "text/html"})
    web.private.add("internal.example")

    status, body = request_json(base_url, "POST", f"/api/tc-library/sources/{bundle}/url", {"url": "https://docs.example.com/prd"})
    assert (status, body["source"]["kind"]) == (201, "url")
    status, body = request_json(base_url, "POST", f"/api/tc-library/sources/{bundle}/url", {"url": "https://internal.example/x"})
    assert (status, body["code"]) == (400, "PRIVATE_ADDRESS")
    status, body = request_json(base_url, "POST", f"/api/tc-library/sources/{bundle}/confluence",
                                {"url": f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}/T"})
    assert (status, body["sources"][0]["ref"]) == (201, f"conf:{PAGE_ID}@v14")
    status, body = request_json(base_url, "POST", f"/api/tc-library/sources/{bundle}/figma", {"url": FIGMA_URL})
    asset = body["source"]["assets"][0]
    with urllib.request.urlopen(f"{base_url}/api/tc-library/sources/{bundle}/assets/{quote(asset)}", timeout=10) as resp:
        assert resp.headers["Content-Type"] == "image/png" and resp.read(4) == b"\x89PNG"
    assert request_json(base_url, "GET", f"/api/tc-library/sources/{bundle}/assets/..%2Fmanifest.json")[0] == 400


def test_source_changes_scan_list_diff_ack(api):
    base_url, bundle, web = api
    setup_confluence(web)
    request_json(base_url, "POST", f"/api/tc-library/sources/{bundle}/confluence", {"url": f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}"})
    import _tc_library as lib
    lib.add_source_refs("야핏무브", "BEN_0002", [f"conf:{PAGE_ID}@v14#§2"])

    setup_confluence(web, version=15, storage=STORAGE_V15)
    scan = request_json(base_url, "POST", f"/api/tc-library/{S}/source-changes/scan")[1]
    assert scan["changes"][0]["case_ids"] == ["BEN_0002"]
    assert request_json(base_url, "GET", f"/api/tc-library/{S}/source-changes")[1]["changes"][0]["to"] == "v15"
    listing = request_json(base_url, "GET", f"/api/tc-library/{S}?needs_review=1")[1]
    assert [c["case_id"] for c in listing["items"]] == ["BEN_0002"]
    diff = request_json(base_url, "GET", "/api/tc-library/source-diff?ref=" + quote(f"conf:{PAGE_ID}@v14#§2"))[1]
    assert any(line["op"] == "+" and "5초마다" in line["text"] for line in diff["lines"])
    case = request_json(base_url, "POST", f"/api/tc-library/{S}/cases/BEN_0002/ack-source")[1]["case"]
    assert "source_change" not in case["flags"]
    assert request_json(base_url, "GET", f"/api/tc-library/{S}/source-changes")[1]["changes"] == []
