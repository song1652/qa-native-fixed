"""TC 스튜디오 생성·검토 화면 실제 브라우저 검증 (Phase 2 W5·W6). 가짜 claude CLI를 쓴다."""
from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest
from playwright.sync_api import Page, expect

from tests.unit.import_studio.import_studio_test_support import dashboard_server
from tests.unit.tc_library.source_fixtures import PRD_MD
from tests.unit.tc_library.test_tc_studio_e2e import _seed


@pytest.fixture
def studio(tmp_path: Path, page: Page, fake_claude):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        _seed(base_url, tmp_path)
        page.goto(base_url + "/tc-studio")
        expect(page.locator("#grid-body tr[data-case]")).to_have_count(6)
        yield base_url, page, tmp_path


def _generate(page: Page, tmp_path: Path) -> None:
    prd = tmp_path / "prd.md"
    prd.write_text(PRD_MD, encoding="utf-8")
    page.locator('[data-id="nav-tab-generate"]').click()
    page.locator('[data-id="src-file-input"]').set_input_files(str(prd))
    expect(page.locator('[data-id="src-chip"]')).to_have_count(1)
    page.locator('[data-id="gen-path-l2"]').select_option("상단 배너")
    page.locator('[data-id="gen-submit"]').click()


# ── W5: 새로 생성 ─────────────────────────────────────────────
def test_generate_job_runs_to_done(studio):
    _, page, tmp_path = studio
    _generate(page, tmp_path)
    expect(page.locator("#job-done")).to_be_visible(timeout=15000)
    expect(page.locator("#job-done-tag")).to_have_text("초안 2건 · 형식 오류 0건")


def test_failed_job_shows_log_and_retry(studio, monkeypatch):
    _, page, tmp_path = studio
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "error")
    _generate(page, tmp_path)
    expect(page.locator("#job-fail")).to_be_visible(timeout=15000)
    expect(page.locator('[data-id="job-log-tail"]')).to_contain_text("CLAUDE_ERROR")
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "ok")
    page.locator('[data-id="job-retry"]').click()
    expect(page.locator("#job-done")).to_be_visible(timeout=15000)


def test_profile_edit_and_save(studio):
    _, page, _ = studio
    page.locator('[data-id="nav-tab-generate"]').click()
    page.locator('[data-id="gen-profile-edit"]').click()
    page.locator('[data-id="gen-rules-input"]').fill("경계값을 모두 쓴다\n금액은 원 단위")
    page.locator('[data-id="gen-profile-name"]').fill("결제 엄격")
    page.locator('[data-id="gen-profile-save"]').click()
    expect(page.locator('[data-id="gen-profile"]')).to_have_value("결제 엄격")
    expect(page.locator("#gen-rules li").first).to_have_text("경계값을 모두 쓴다")
