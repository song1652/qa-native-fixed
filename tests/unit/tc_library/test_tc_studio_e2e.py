"""TC 스튜디오 실제 브라우저 검증 (로드맵 W1~W7). 실행: .venv/bin/python -m pytest tests/unit/tc_library/test_tc_studio_e2e.py"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import Page, expect

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
from tests.unit.tc_library.tc_fixtures import build_template_workbook

S = quote("야핏무브")


def _seed(base_url: str, tmp_path: Path) -> None:
    data = build_template_workbook(tmp_path / "seed.xlsx").read_bytes()
    req = urllib.request.Request(
        base_url + "/api/tc-library/import/preview?filename=" + quote("야핏무브_Full.xlsx"),
        data=data, method="POST", headers={"Content-Type": "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        preview = json.loads(resp.read())
    status, body = request_json(base_url, "POST", "/api/tc-library/import", {
        "preview_id": preview["preview_id"], "suite": "야핏무브", "sheets": ["혜택", "홈"],
        "prefixes": {"혜택": "BEN", "홈": "HOME"}})
    assert status == 200, body


@pytest.fixture
def studio(tmp_path: Path, page: Page):
    import _paths
    original_paths = {name: getattr(_paths, name) for name in ("PROJECT_ROOT", "TESTCASES_DIR", "TC_LIBRARY_DIR")}
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        _seed(base_url, tmp_path)
        page.goto(base_url + "/tc-studio")
        expect(page.locator("#grid-body tr[data-case]")).to_have_count(6)
        yield base_url, page
    assert {name: getattr(_paths, name) for name in original_paths} == original_paths


def rows(page: Page):
    return page.locator("#grid-body tr[data-case]")


# ── W1: 셸·라이브러리·상세 ──────────────────────────────────────────────────────────
def test_route_sidebar_and_tabs(studio):
    _, page = studio
    expect(page.locator("#tab-tc_studio")).to_have_class(re.compile("active"))
    expect(page.locator('[data-id="suite-select"] option')).to_have_text(["야핏무브 (6)"])
    expect(page.locator('[data-id="nav-tab-library"]')).to_be_visible()
    expect(page.locator('[data-id="nav-tab-generate"]')).to_be_visible()
    expect(page.locator('[data-id="nav-tab-review"]')).to_be_visible()


def test_tree_filters_and_search(studio):
    _, page = studio
    page.locator('[data-id="tree-node"][data-name="상단 배너"]').click()
    expect(rows(page)).to_have_count(2)
    expect(page.locator("#grid-crumb")).to_have_text("혜택 › 혜택 탭 › 상단 배너")
    page.locator('[data-id="lib-filter-reset"]').click()
    page.locator('[data-id="lib-search"]').fill("돈불리기")
    expect(rows(page)).to_have_count(2)
    page.locator('[data-id="lib-filter-reset"]').click()
    page.locator('[data-id="lib-filter-result"]').select_option("fail")
    expect(rows(page)).to_have_count(1)
    page.locator('[data-id="lib-filter-result"]').select_option("none")
    expect(rows(page)).to_have_count(3)


def test_chip_and_cell_edits_persist(studio):
    _, page = studio
    row = page.locator('tr[data-case="BEN_0002"]')
    row.locator('[data-id="grid-cell-priority"]').select_option("P3")
    expect(page.locator(".toast.ok").first).to_contain_text("BEN_0002 저장됨")
    cell = row.locator('[data-id="grid-cell-feature"]')
    cell.dblclick()
    page.keyboard.press("ControlOrMeta+a")
    page.keyboard.type("배너 가로 스크롤")
    page.keyboard.press("ControlOrMeta+Enter")
    expect(page.locator(".toast.ok").last).to_contain_text("rev 3")
    page.reload()
    row = page.locator('tr[data-case="BEN_0002"]')
    expect(row.locator('[data-id="grid-cell-priority"]')).to_have_value("P3")
    expect(row.locator('[data-id="grid-cell-feature"]')).to_have_text("배너 가로 스크롤")


def test_stale_rev_shows_conflict_toast(studio):
    base_url, page = studio
    request_json(base_url, "PATCH", f"/api/tc-library/{S}/cases/BEN_0003", {"rev": 1, "priority": "P0"})
    page.locator('tr[data-case="BEN_0003"] [data-id="grid-cell-priority"]').select_option("P2")
    expect(page.locator('[data-id="toast-conflict-reload"]')).to_be_visible()
    page.locator('[data-id="toast-conflict-reload"]').click()
    expect(page.locator('tr[data-case="BEN_0003"] [data-id="grid-cell-priority"]')).to_have_value("P0")


def test_bulk_add_delete_and_undo(studio):
    _, page = studio
    rows(page).nth(0).locator('[data-id="grid-row-check"]').check()
    rows(page).nth(1).locator('[data-id="grid-row-check"]').check()
    expect(page.locator('[data-id="bulk-bar"]')).to_contain_text("2건 선택")
    page.locator('[data-id="bulk-priority"]').select_option("P2")
    expect(page.locator('tr[data-case="BEN_0002"] [data-id="grid-cell-priority"]')).to_have_value("P2")

    page.locator('[data-id="btn-add-case"]').click()
    expect(rows(page)).to_have_count(7)
    expect(page.locator('[data-id="detail-panel"] #d-id')).to_have_text("BEN_0006")

    page.locator('[data-id="detail-delete"]').click()
    page.locator('[data-id="confirm-ok"]').click()
    expect(rows(page)).to_have_count(6)
    page.locator('[data-id="delete-undo"]').click()
    expect(rows(page)).to_have_count(7)


def test_detail_save_history_and_revert(studio):
    _, page = studio
    # Phase 3의 배너 응답을 늦춰 저장 중 선택한 이력 탭이 유지되는지 재현한다.
    page.evaluate("""() => {
        const watch = window.TCS_NS.sourceWatch;
        if (!watch) return;
        const original = watch.renderBanner;
        watch.renderBanner = async (...args) => {
            await new Promise((resolve) => setTimeout(resolve, 1000));
            return original(...args);
        };
    }""")
    page.locator('tr[data-case="HOME_0001"] td.no').click()
    expect(page.locator("#d-id")).to_have_text("HOME_0001")
    page.locator('[data-id="detail-expected"]').fill("홈 화면 상단에 D+3 전용 카드가 노출된다.")
    page.locator('[data-id="detail-step-add"]').click()
    page.locator('[data-id="detail-step-input"]').last.fill("홈 카드 선택")
    page.locator('[data-id="detail-save"]').click()
    expect(page.locator("#d-rev")).to_have_text("rev 2")
    page.locator('[data-id="detail-tab-history"]').click()
    history = page.locator('[data-id="detail-history"] li')
    expect(history.first).to_contain_text("expected")
    expect(page.locator('[data-id="detail-save"]')).not_to_have_class(re.compile("loading"))
    page.locator('[data-id="detail-history-revert"]').first.click()
    expect(page.locator("#d-rev")).to_have_text("rev 3")


# ── W2: 엑셀 가져오기 모달 ───────────────────────────────────────────────
def test_import_modal_previews_and_imports_workbook(tmp_path, page):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        page.goto(base_url + "/tc-studio")
        page.locator('[data-id="empty-import-xlsx"]').click()
        expect(page.locator('[data-id="import-modal"]')).to_be_visible()
        assert page.evaluate("""async () => {
            const modal = document.querySelector('[data-id="import-modal"]');
            await refreshAll();
            return modal === document.querySelector('[data-id="import-modal"]') && !modal.hidden;
        }""")
        xlsx = build_template_workbook(tmp_path / "야핏무브_Full.xlsx")
        page.locator('[data-id="import-file-input"]').set_input_files(xlsx)
        expect(page.locator('[data-id="import-confirm"]')).to_have_text("6건 가져오기")
        expect(page.locator('[data-id="import-sheets"] input[type=checkbox]')).to_have_count(2)
        page.locator('[data-prefix="혜택"]').fill("BEN")
        page.locator('[data-prefix="홈"]').fill("HOME")
        page.locator('[data-id="import-confirm"]').click()
        expect(page.locator('[data-id="import-modal"]')).to_be_hidden()
        expect(rows(page)).to_have_count(6)
        expect(page.locator('[data-id="suite-select"] option')).to_have_text(["야핏무브 (6)"])
        expect(page.locator('tr[data-case="BEN_0001"]')).to_be_visible()
        page.reload()
        expect(rows(page)).to_have_count(6)

# ── W3: 내보내기 화면 ──────────────────────────────────────────────────────────
def test_export_check_and_download(studio):
    _, page = studio
    page.locator('[data-id="nav-tab-export"]').click()
    page.locator('[data-id="xlsx-run-check"]').click()
    expect(page.locator('[data-id="xlsx-integrity"] li .ok')).to_have_count(4)
    expect(page.locator('[data-id="xlsx-download"]')).to_be_enabled()
    with page.expect_download() as info:
        page.locator('[data-id="xlsx-download"]').click()
    assert info.value.suggested_filename.endswith(".xlsx")
