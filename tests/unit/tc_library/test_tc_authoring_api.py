from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import quote

import openpyxl
import pytest

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
from tests.unit.tc_library.source_fixtures import PRD_MD
from tests.unit.tc_library.test_tc_library_api import _post_bytes
from tests.unit.tc_library.tc_fixtures import build_template_workbook

S = quote("야핏무브")


@pytest.fixture
def api(tmp_path: Path, fake_claude):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        xlsx = build_template_workbook(tmp_path / "src.xlsx").read_bytes()
        _, preview = _post_bytes(base_url, "/api/tc-library/import/preview?filename=a.xlsx", xlsx)
        request_json(base_url, "POST", "/api/tc-library/import", {
            "preview_id": preview["preview_id"], "suite": "야핏무브", "sheets": ["혜택", "홈"],
            "prefixes": {"혜택": "BEN", "홈": "HOME"}})
        yield base_url


def _bundle_with_prd(base_url: str) -> tuple[str, dict]:
    status, body = request_json(base_url, "POST", "/api/tc-library/sources")
    assert status == 201
    bundle = body["bundle_id"]
    status, added = _post_bytes(base_url, f"/api/tc-library/sources/{bundle}/file?filename=prd.md", PRD_MD.encode())
    assert status == 201, added
    return bundle, added["source"]


def _wait(base_url: str, job_id: str) -> dict:
    for _ in range(100):
        body = request_json(base_url, "GET", f"/api/tc-library/jobs/{job_id}")[1]
        if body["job"]["status"] not in ("queued", "fetching", "drafting", "validating"):
            return body
        time.sleep(0.1)
    raise AssertionError("job did not finish")


def test_sources_paste_remove_and_excerpt(api):
    bundle, source = _bundle_with_prd(api)
    status, pasted = request_json(api, "POST", f"/api/tc-library/sources/{bundle}/paste", {"text": "붙여넣은 기획\n본문"})
    assert (status, pasted["source"]["kind"]) == (201, "paste")
    manifest = request_json(api, "GET", f"/api/tc-library/sources/{bundle}")[1]
    assert [s["kind"] for s in manifest["sources"]] == ["file", "paste"]
    ex = request_json(api, "GET", f"/api/tc-library/sources/{bundle}/excerpt?ref=" + quote(source["ref"] + "#§2"))[1]
    assert ex["section"] == "배너 롤링 규칙"
    assert request_json(api, "DELETE", f"/api/tc-library/sources/{bundle}/s02")[0] == 200
    assert _post_bytes(api, f"/api/tc-library/sources/{bundle}/file?filename=a.exe", b"MZ")[0] == 400


def test_job_runs_to_done_and_drafts_are_listed(api):
    bundle, _ = _bundle_with_prd(api)
    status, body = request_json(api, "POST", f"/api/tc-library/{S}/jobs", {
        "bundle_id": bundle, "sheet": "혜택", "path": ["혜택 탭", "상단 배너"], "profile": "기본"})
    assert status == 202
    done = _wait(api, body["job"]["job_id"])
    assert (done["job"]["status"], done["job"]["kept"]) == ("done", 2)
    assert "status=done" in done["log"]
    drafts = request_json(api, "GET", f"/api/tc-library/{S}?status=draft&job={done['job']['job_id']}")[1]
    assert drafts["total"] == 2


def test_second_job_is_rejected_while_running(api, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "slow")
    bundle, _ = _bundle_with_prd(api)
    payload = {"bundle_id": bundle, "sheet": "혜택", "path": ["혜택 탭"], "profile": "기본"}
    first = request_json(api, "POST", f"/api/tc-library/{S}/jobs", payload)[1]["job"]["job_id"]
    status, body = request_json(api, "POST", f"/api/tc-library/{S}/jobs", payload)
    assert (status, body["code"]) == (409, "JOB_RUNNING")
    request_json(api, "POST", f"/api/tc-library/jobs/{first}/cancel")
    assert _wait(api, first)["job"]["status"] == "cancelled"


def test_profiles_coverage_and_resolve_duplicate(api):
    assert [p["name"] for p in request_json(api, "GET", "/api/tc-library/profiles")[1]["profiles"]] == ["기본"]
    status, saved = request_json(api, "PUT", "/api/tc-library/profiles/" + quote("엄격"), {"rules": ["경계값"], "coverage": {"positive": 1, "negative": 1, "validation_if_input": 1}})
    assert (status, saved["profile"]["rules"]) == (200, ["경계값"])
    cov = request_json(api, "GET", f"/api/tc-library/{S}/coverage?sheet=" + quote("혜택") + "&path=" + quote("혜택 탭/신규회원 한정 혜택"))[1]
    assert cov["features"][0]["missing"] == []
    cov = request_json(api, "GET", f"/api/tc-library/{S}/coverage?sheet=" + quote("혜택") + "&path=" + quote("혜택 탭/신규회원 한정 혜택") + "&profile=" + quote("엄격"))[1]
    assert cov["features"][0]["missing"] == ["정상"]
    created = request_json(api, "POST", f"/api/tc-library/{S}/cases", {"sheet": "혜택", "path": ["혜택 탭", "상단 배너", ""], "feature": "배너 스크롤", "steps": ["혜택 탭 선택"], "expected": "상단에 광고 배너가 가로 스크롤 동작되어 노출된다."})[1]["case"]
    status, body = request_json(api, "POST", f"/api/tc-library/{S}/cases/{created['case_id']}/resolve-duplicate", {"rev": 1, "action": "skip"})
    assert (status, body["draft"]["status"]) == (200, "rejected")


def test_custom_mapping_import_and_reserved_suite(api, tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "로그인"
    ws.append(["ID", "제목", "절차", "기대 결과"])
    ws.append(["L-1", "로그인 성공", "1. 아이디 입력\n2. 로그인 선택", "홈으로 이동한다."])
    path = tmp_path / "other.xlsx"
    wb.save(path)
    mapping = quote(json.dumps({"header_row": 1, "columns": {"feature": "B", "steps": "C", "expected": "D"}}))
    status, preview = _post_bytes(api, f"/api/tc-library/import/preview?filename=other.xlsx&mapping={mapping}", path.read_bytes())
    assert (status, preview["sheets"][0]["cases"]) == (200, 1), preview
    status, body = request_json(api, "POST", "/api/tc-library/import", {
        "preview_id": preview["preview_id"], "suite": "웹", "sheets": ["로그인"], "prefixes": {"로그인": "LOG"}})
    assert body["created"] == 1
    case = request_json(api, "GET", "/api/tc-library/" + quote("웹") + "/cases/LOG_0001")[1]["case"]
    assert (case["path"][0], case["steps"]) == ("로그인", ["아이디 입력", "로그인 선택"])
    bad = quote(json.dumps({"columns": {"feature": "B"}}))
    assert _post_bytes(api, f"/api/tc-library/import/preview?filename=o.xlsx&mapping={bad}", path.read_bytes())[1]["code"] == "MAPPING_INCOMPLETE"
    assert request_json(api, "GET", "/api/tc-library/jobs/tree")[0] in (400, 404)
    assert request_json(api, "POST", "/api/tc-library/profiles/cases", {})[0] in (400, 404)
