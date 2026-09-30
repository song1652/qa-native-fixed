"""TC 스튜디오 원격 소스·연결 설정·출처 변경 화면 (Phase 3 W9·W10). 네트워크 대신 fake_web을 쓴다."""
from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

import _tc_library as lib
from tests.unit.import_studio.import_studio_test_support import dashboard_server
from tests.unit.tc_library.connector_fixtures import (
    CLOUD, FIGMA_URL, PAGE_ID, STORAGE_V15, setup_confluence, setup_figma,
)
from tests.unit.tc_library.test_tc_studio_e2e import _seed


@pytest.fixture
def studio(tmp_path: Path, page: Page, fake_web, fake_claude):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        _seed(base_url, tmp_path)
        page.goto(base_url + "/tc-studio")
        expect(page.locator("#grid-body tr[data-case]")).to_have_count(6)
        yield base_url, page, fake_web


def _open_tab(page: Page, tab: str) -> None:
    page.locator('[data-id="nav-tab-generate"]').click()
    page.locator(f'[data-id="src-tab-{tab}"]').click()


# ── W9: 원격 소스 탭 · 연결 설정 ────────────────────────────────
def test_settings_modal_saves_without_showing_token(studio):
    _, page, web = studio
    page.locator('[data-id="nav-tab-generate"]').click()
    expect(page.locator('[data-id="cred-status-confluence"]')).to_have_text("Confluence 미연결")
    page.locator('[data-id="cred-settings"]').click()
    page.locator('[data-id="cred-base"]').fill(CLOUD)
    page.locator('[data-id="cred-email"]').fill("qa.lead@yafit.com")
    page.locator('[data-id="cred-conf-token"]').fill("secret-token")
    page.locator('[data-id="cred-save"]').click()
    expect(page.locator('[data-id="cred-status-confluence"]')).to_have_text("Confluence 연결됨 · qa****@yafit.com")
    assert "secret-token" not in page.content()


def test_confluence_url_and_figma_sources(studio):
    _, page, web = studio
    setup_confluence(web)
    setup_figma(web)
    web.add("https://docs.example.com/prd", "<title>PRD</title><h1>배너</h1><p>본문</p>", headers={"Content-Type": "text/html"})
    page.reload()
    _open_tab(page, "confluence")
    page.locator('[data-id="src-confluence-url"]').fill(f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}/T")
    page.locator('[data-id="src-confluence-fetch"]').click()
    expect(page.locator('[data-id="src-chip"]')).to_have_count(1)
    expect(page.locator('[data-id="src-chip"] .src-ref').first).to_have_text(f"conf:{PAGE_ID}@v14")
    page.locator('[data-id="src-tab-figma"]').click()
    page.locator('[data-id="src-figma-url"]').fill(FIGMA_URL)
    page.locator('[data-id="src-figma-fetch"]').click()
    page.locator('[data-id="src-tab-url"]').click()
    page.locator('[data-id="src-url-url"]').fill("https://docs.example.com/prd")
    page.locator('[data-id="src-url-fetch"]').click()
    expect(page.locator('[data-id="src-chip"]')).to_have_count(3)


def test_figma_draft_shows_frame_in_review(studio):
    _, page, web = studio
    setup_figma(web)
    page.reload()
    _open_tab(page, "figma")
    page.locator('[data-id="src-figma-url"]').fill(FIGMA_URL)
    page.locator('[data-id="src-figma-fetch"]').click()
    expect(page.locator('[data-id="src-chip"]')).to_have_count(1)
    page.locator('[data-id="gen-path-l2"]').select_option("상단 배너")
    page.locator('[data-id="gen-submit"]').click()
    page.locator('[data-id="job-open-review"]').click(timeout=15000)
    expect(page.locator('[data-id="source-figma-frame"] img')).to_have_count(1)
    expect(page.locator('[data-id="draft-card"]').first).not_to_contain_text("추정")

# ── W10: 출처 변경 배너 · 차이 · 확인 ───────────────────────────
def test_source_change_banner_diff_and_ack(studio):
    base_url, page, web = studio
    setup_confluence(web)
    import _tc_sources as src
    import _tc_connectors as conn
    conn.add_confluence(src.new_bundle(), f"{CLOUD}/wiki/spaces/MOVE/pages/{PAGE_ID}")
    lib.add_source_refs("야핏무브", "BEN_0002", [f"conf:{PAGE_ID}@v14#§2"])
    setup_confluence(web, version=15, storage=STORAGE_V15)
    page.reload()

    page.locator('[data-id="btn-check-sources"]').click()
    expect(page.locator('[data-id="banner-source-changed"]')).to_contain_text("v14 → v15")
    page.locator('[data-id="banner-review-now"]').click()
    expect(page.locator("#grid-body tr[data-case]")).to_have_count(1)
    page.locator('tr[data-case="BEN_0002"] td.no').click()
    page.locator('[data-id="detail-tab-source"]').click()
    expect(page.locator('[data-id="detail-source-diff"] ins')).to_contain_text("5초마다")
    page.locator('[data-id="detail-mark-reviewed"]').click()
    expect(page.locator('[data-id="banner-source-changed"]')).to_have_count(0)
    assert f"conf:{PAGE_ID}@v15#§2" in lib.get_case("야핏무브", "BEN_0002")["source_refs"]
