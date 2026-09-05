from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import csv
import io
import json
from pathlib import Path
import urllib.request

import pytest

from tests.import_studio_test_support import (
    dashboard_server,
    materialize_workbooks,
    request_json,
)


MAPPINGS = {
    "tc_id": "A열",
    "title": "B열",
    "steps": "C열",
    "expected": "D열",
}


@pytest.fixture
def profile_api(tmp_path: Path):
    project = tmp_path / "project"
    materialize_workbooks(project / "import")
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        yield base_url, project


def _create_profile(base_url: str, name: str) -> str:
    status, body = request_json(
        base_url, "POST", "/api/import/profiles", {"name": name, "mappings": MAPPINGS}
    )
    assert status == 201, body
    return body["id"]


def test_rest_and_compatibility_profile_mutations_share_the_lock(profile_api):
    base_url, _ = profile_api
    first_id = _create_profile(base_url, "first")
    second_id = _create_profile(base_url, "second")

    def update_first(index: int):
        return request_json(
            base_url,
            "PUT",
            f"/api/import/profiles/{first_id}",
            {"name": f"first-{index}"},
        )

    def update_second(index: int):
        return request_json(
            base_url,
            "POST",
            "/api/import/profiles/update",
            {"id": second_id, "name": f"second-{index}"},
        )

    jobs = [
        (update_first if index % 2 == 0 else update_second, index)
        for index in range(16)
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda job: job[0](job[1]), jobs))

    assert all(status == 200 and body["ok"] for status, body in results)
    status, body = request_json(base_url, "GET", "/api/import/profiles")
    assert status == 200, body
    profiles = {profile["id"]: profile for profile in body["profiles"]}
    assert set(profiles) == {first_id, second_id}
    assert profiles[first_id]["name"].startswith("first-")
    assert profiles[second_id]["name"].startswith("second-")


def test_corrupt_profile_store_is_reported_instead_of_becoming_empty(profile_api):
    base_url, project = profile_api
    profile_path = project / "state" / "import_profiles.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text("{not-json", encoding="utf-8")

    status, body = request_json(base_url, "GET", "/api/import/profiles")

    assert status == 500
    assert body["ok"] is False
    assert body["code"] == "PROFILE_STORE_ERROR"


def test_files_endpoint_returns_sheet_name_strings(profile_api):
    base_url, _ = profile_api

    status, body = request_json(base_url, "GET", "/api/import/files")

    assert status == 200, body
    assert body["files"]
    assert all(isinstance(sheet, str) for file in body["files"] for sheet in file["sheets"])


def test_files_endpoint_exposes_corrupt_workbook_error(profile_api):
    base_url, project = profile_api
    (project / "import" / "corrupt.xlsx").write_bytes(b"not an xlsx archive")

    status, body = request_json(base_url, "GET", "/api/import/files")

    assert status == 200, body
    corrupt = next(file for file in body["files"] if file["name"] == "corrupt.xlsx")
    assert corrupt["sheets"] == []
    assert corrupt["error"]


def test_legacy_preview_csv_neutralizes_formula_cells(profile_api):
    base_url, project = profile_api
    session_id = "sess_formula"
    session_path = project / "state" / "import_sessions" / f"{session_id}.json"
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(json.dumps({"rows": [{
        "_row": 2,
        "tc_id": "SAFE_1",
        "title": "\t=HYPERLINK(\"https://example.invalid\")",
        "group": "safe",
        "status": "error",
        "reason": "@SUM(1,1)",
    }]}), encoding="utf-8")

    with urllib.request.urlopen(
        f"{base_url}/api/import/preview/csv?session_id={session_id}", timeout=10
    ) as response:
        rows = list(csv.reader(io.StringIO(response.read().decode("utf-8"))))

    assert rows[1][2].startswith("'\t=")
    assert rows[1][5].startswith("'@")
