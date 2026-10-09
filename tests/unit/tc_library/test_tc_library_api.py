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
        [{"suite": "야핏무브", "sheets": ["혜택", "홈"], "count": 6, "imported": 6, "protected": False}]
    tree = request_json(base_url, "GET", f"/api/tc-library/{S}/tree")[1]["tree"]
    assert [(n["name"], n["count"]) for n in tree] == [("혜택", 5), ("홈", 1)]
    listing = request_json(base_url, "GET",
                           f"/api/tc-library/{S}?path=" + quote("혜택/혜택 탭/상단 배너"))[1]
    assert (listing["total"], [c["case_id"] for c in listing["items"]]) == (2, ["BEN_0002", "BEN_0003"])
    not_run = request_json(base_url, "GET", f"/api/tc-library/{S}?execution_result=")[1]
    assert [c["case_id"] for c in not_run["items"]] == ["BEN_0001", "BEN_0004", "HOME_0001"]
    case = request_json(base_url, "GET", f"/api/tc-library/{S}/cases/BEN_0002")[1]["case"]
    assert [i["code"] for i in case["issues"]] == ["PRIORITY_EMPTY"]


def test_patch_conflict_and_revert(api):
    base_url, _ = api
    path = f"/api/tc-library/{S}/cases/BEN_0002"
    status, body = request_json(base_url, "PATCH", path, {"rev": 1, "priority": "P1"})
    assert (status, body["case"]["rev"]) == (200, 2)
    status, body = request_json(base_url, "PATCH", path, {"rev": 1, "priority": "P2"})
    assert (status, body["code"], body["server_case"]["priority"]) == (409, "REV_CONFLICT", "P1")

    history = request_json(base_url, "GET", path + "/history")[1]["history"]
    hid = next(e["history_id"] for e in history if e["field"] == "priority")
    status, body = request_json(base_url, "POST", path + "/revert", {"history_id": hid, "rev": 2})
    assert (status, body["case"]["priority"]) == (200, "")


def test_bulk_create_duplicate_move_delete_restore(api):
    base_url, _ = api
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/bulk", {
        "items": [{"case_id": "BEN_0001", "rev": 1}, {"case_id": "BEN_0002", "rev": 9}],
        "op": "set", "field": "priority", "value": "P2"})
    assert (body["updated"], [c["case_id"] for c in body["conflicts"]]) == (["BEN_0001"], ["BEN_0002"])

    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/cases", {
        "sheet": "혜택", "path": ["혜택 탭", "상단 배너", ""], "feature": "새 기능", "after": "BEN_0003"})
    assert (status, body["case"]["case_id"]) == (201, "BEN_0006")
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/cases/BEN_0001/duplicate")
    assert (status, body["case"]["case_id"]) == (201, "BEN_0007")
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/move", {
        "items": [{"case_id": "BEN_0006", "rev": 1}], "sheet": "혜택",
        "path": ["혜택 탭", "신규회원 한정 혜택", "돈불리기"]})
    assert body["moved"] == ["BEN_0006"]

    assert request_json(base_url, "DELETE", f"/api/tc-library/{S}/cases/BEN_0003?rev=9")[0] == 409
    assert request_json(base_url, "DELETE", f"/api/tc-library/{S}/cases/BEN_0003?rev=1")[0] == 200
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/cases/BEN_0003/restore")
    assert (status, body["case"]["rev"]) == (200, 3)
def test_export_and_download(api):
    base_url, _ = api
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/export/xlsx",
                                {"scope": "all", "history_note": "Phase 1"})
    assert status == 200 and body["count"] == 6
    assert {c["level"] for c in body["checks"]} == {"ok"}, body["checks"]
    with urllib.request.urlopen(
            f"{base_url}/api/tc-library/exports/{body['export_id']}/download", timeout=10) as resp:
        assert resp.read(2) == b"PK"
        assert "filename*=UTF-8''" in resp.headers["Content-Disposition"]
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


def test_blank_starter_is_explicit_and_ready_for_authoring(tmp_path: Path):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        assert request_json(base_url, "GET", "/api/tc-library")[1]["suites"] == []
        status, started = request_json(base_url, "POST", "/api/tc-library/starter")
        assert (status, started["suite"]) == (201, "기본양식")
        assert request_json(base_url, "POST", "/api/tc-library/starter")[0] == 200
        suites = request_json(base_url, "GET", "/api/tc-library")[1]["suites"]
        assert [(s["suite"], s["sheets"], s["count"]) for s in suites] == [("기본양식", ["테스트케이스"], 0)]
        status, _ = request_json(base_url, "POST", "/api/tc-library/" + quote("기본양식") + "/branches",
                                 {"sheet": "테스트케이스", "path": ["로그인", "", ""]})
        assert status == 200
