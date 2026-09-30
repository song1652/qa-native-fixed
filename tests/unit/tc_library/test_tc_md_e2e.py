"""TC 스튜디오 md 내보내기 화면 (Phase 4 W12)."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import Page, expect

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
from tests.unit.tc_library.test_tc_studio_e2e import _seed

S = quote("야핏무브")


@pytest.fixture
def studio(tmp_path: Path, page: Page):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    (project / "config").mkdir()
    (project / "config" / "pages.json").write_text(json.dumps({"yafit_benefit": "https://m.yafit.example/b"}), encoding="utf-8")
    with dashboard_server(project) as base_url:
        _seed(base_url, tmp_path)
        for case_id in ("BEN_0001", "BEN_0002"):
            request_json(base_url, "PATCH", f"/api/tc-library/{S}/cases/{case_id}", {"rev": 1, "priority": "P0"})
        page.goto(base_url + "/tc-studio")
        page.locator('[data-id="nav-tab-export"]').click()
        yield base_url, page, project


# ── W12: md 카드 ────────────────────────────────────────────────
def test_map_preview_commit_and_rollback(studio):
    _, page, project = studio
    expect(page.locator('[data-id="md-eligibility"] .v').last).to_have_text("0")
    page.locator('[data-id="md-map-code"]').first.fill("YFB")
    page.locator('[data-id="md-map-fix"]').first.click()
    expect(page.locator('[data-id="md-eligibility"] .v').last).to_have_text("5")
    page.locator('[data-id="md-preview"]').click()
    expect(page.locator('[data-id="md-preview-panel"] tbody tr')).to_have_count(5)
    page.locator('[data-id="md-commit"]').click()
    expect(page.locator("#md-result-text")).to_have_text("반영 완료 · 신규 5 · 갱신 0")
    assert len(list((project / "testcases" / "yafit_benefit").glob("tc_YFB_*.md"))) == 5
    page.locator('[data-id="md-rollback"]').click()
    expect(page.locator('[data-id="md-preview-panel"]')).to_be_hidden()
    assert not list((project / "testcases" / "yafit_benefit").glob("tc_YFB_*.md"))


def test_drifted_file_needs_a_decision(studio):
    base_url, page, project = studio
    request_json(base_url, "PUT", f"/api/tc-library/{S}/md-groups", {"path": ["혜택", "혜택 탭"], "group": "yafit_benefit", "code": "YFB"})
    run = request_json(base_url, "POST", f"/api/tc-library/{S}/export/md")[1]
    request_json(base_url, "POST", f"/api/tc-library/{S}/md-exports/{run['run_id']}/commit", {"skip": []})
    target = next((project / "testcases" / "yafit_benefit").glob("tc_YFB_01_*.md"))
    target.write_text(target.read_text(encoding="utf-8") + "\n사람이 고친 줄\n", encoding="utf-8")

    page.reload()
    page.locator('[data-id="nav-tab-export"]').click()
    expect(page.locator('[data-id="md-drift-warning"]')).to_contain_text("직접 바뀐 파일 1개")
    page.locator('[data-id="md-preview"]').click()
    expect(page.locator('[data-id="md-commit"]')).to_be_disabled()
    page.locator('[data-id="md-conflict-decision"]').select_option("skip")
    page.locator('[data-id="md-commit"]').click()
    expect(page.locator("#md-result-text")).to_contain_text("건너뜀 1")
    assert "사람이 고친 줄" in target.read_text(encoding="utf-8")
