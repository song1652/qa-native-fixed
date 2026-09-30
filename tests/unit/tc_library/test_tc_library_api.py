from __future__ import annotations

import http.client
import json
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, urlparse

import pytest

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
from tests.unit.tc_library.tc_fixtures import build_template_workbook

S = quote("야핏무브")


def _post_bytes(base_url: str, path: str, data: bytes) -> tuple[int, dict]:
    req = urllib.request.Request(base_url + path, data=data, method="POST",
                                 headers={"Content-Type": "application/octet-stream"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read())


@pytest.fixture
def api(tmp_path: Path):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        xlsx = build_template_workbook(tmp_path / "src.xlsx").read_bytes()
        status, preview = _post_bytes(
            base_url, "/api/tc-library/import/preview?filename=" + quote("야핏무브_Full.xlsx"), xlsx)
        assert status == 200, preview
        status, body = request_json(base_url, "POST", "/api/tc-library/import", {
            "preview_id": preview["preview_id"], "suite": "야핏무브",
            "sheets": ["혜택", "홈"], "prefixes": {"혜택": "BEN", "홈": "HOME"}})
        assert (status, body["created"]) == (200, 6), body
        yield base_url, preview


def test_import_preview_describes_sheets(api):
    _, preview = api
    assert [(s["name"], s["header_row"], s["cases"]) for s in preview["sheets"]] == \
        [("혜택", 11, 5), ("홈", 11, 1)]


def test_import_preview_rejects_non_xlsx_and_oversized_body(api):
    base_url, _ = api
    assert _post_bytes(base_url, "/api/tc-library/import/preview?filename=a.xlsx", b"hello")[0] == 400
    parsed = urlparse(base_url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=10)
    conn.putrequest("POST", "/api/tc-library/import/preview?filename=a.xlsx")
    conn.putheader("Content-Length", str(30 * 1024 * 1024))
    conn.endheaders()
    response = conn.getresponse()
    assert (response.status, json.loads(response.read())["code"]) == (413, "PAYLOAD_TOO_LARGE")
    conn.close()


def test_read_endpoints(api):
    base_url, _ = api
    assert request_json(base_url, "GET", "/api/tc-library")[1]["suites"] == \
        [{"suite": "야핏무브", "sheets": ["혜택", "홈"], "count": 6}]
    tree = request_json(base_url, "GET", f"/api/tc-library/{S}/tree")[1]["tree"]
    assert [(n["name"], n["count"]) for n in tree] == [("혜택", 5), ("홈", 1)]
    listing = request_json(base_url, "GET",
                           f"/api/tc-library/{S}?path=" + quote("혜택/혜택 탭/상단 배너"))[1]
    assert (listing["total"], [c["case_id"] for c in listing["items"]]) == (2, ["BEN_0002", "BEN_0003"])
    not_run = request_json(base_url, "GET", f"/api/tc-library/{S}?execution_result=")[1]
    assert [c["case_id"] for c in not_run["items"]] == ["BEN_0001", "BEN_0004", "HOME_0001"]
    case = request_json(base_url, "GET", f"/api/tc-library/{S}/cases/BEN_0002")[1]["case"]
    assert [i["code"] for i in case["issues"]] == ["PRIORITY_EMPTY"]


def test_rejects_bad_suite_and_cross_origin_writes(api):
    base_url, _ = api
    status, body = request_json(base_url, "GET", "/api/tc-library/..%2Fetc/tree")
    assert (status, body["code"]) == (400, "INVALID_SUITE")
    req = urllib.request.Request(f"{base_url}/api/tc-library/{S}/cases/BEN_0001", method="PATCH",
                                 data=b'{"rev": 1}', headers={"Origin": "http://evil.example",
                                                              "Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as err:
        urllib.request.urlopen(req, timeout=10)
    assert err.value.code == 403
