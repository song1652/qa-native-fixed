"""모든 대시보드 화면은 같은 배치로 시작한다 — 제목 위치·크기·글꼴과 본문 폭.

화면마다 가운데 박스·다른 여백·다른 제목 크기를 쓰면 탭을 옮길 때 제목이 튄다(2026-10-01 정리).
새 화면을 추가하면 VIEWS에 넣는다.
"""
from __future__ import annotations

import sys
import json
import pytest
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from tests.unit.import_studio.import_studio_test_support import dashboard_server  # noqa: E402


def test_skipped_healing_is_not_reported_as_retry_limit(tmp_path):
    from playwright.sync_api import expect
    with dashboard_server(tmp_path / "project") as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.route('**/api/quick_state*', lambda route: route.fulfill(json={
            "status": "heal_failed", "execution_result": {
                "total": 3, "passed": 1, "failed": 2, "pass_rate": 33.3,
                "heal_count": 0, "heal_decision": "skip", "group_results": {},
            },
        }))
        page.goto(base + "/")
        page.wait_for_function("quickState && quickState.execution_result")
        page.locator('#tab-quick_run').click()
        expect(page.locator('.quick-heal-banner')).to_contain_text('힐링 생략')
        expect(page.locator('.quick-heal-banner')).not_to_contain_text('최대 힐링 횟수 초과')
        browser.close()


@pytest.mark.parametrize("notification", ["single_init", "parallel"])
def test_automatic_pipeline_notice_does_not_block_page_management(tmp_path, notification):
    with dashboard_server(tmp_path / "project") as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(base + "/")
        page.evaluate("kind => showHookAlert(kind, '실행 준비 완료')", notification)
        assert page.locator('#hook-alert').count() == 0
        page.locator('#tab-pages').click()
        assert page.locator('#pg-url').is_visible()
        browser.close()


def test_overview_counts_registered_pages_instead_of_case_folders(tmp_path):
    project = tmp_path / "project"
    (project / "testcases" / "unregistered").mkdir(parents=True)
    (project / "config").mkdir()
    (project / "config" / "pages.json").write_text(json.dumps({
        "_comment": "Not a page",
        "login": "https://example.com/login",
        "cart": {"url": "https://example.com/cart"},
    }), encoding="utf-8")
    with dashboard_server(project) as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(base + "/")
        page.wait_for_function("pagesData.pages && pagesData.pages.cart")
        page.evaluate("selectView('')")
        summary = page.locator('.ov-summary-item').filter(has_text="등록된 페이지")
        assert summary.locator('.ov-summary-value').inner_text() == "2"
        page.evaluate("selectView('pages')")
        assert page.locator('.pages-list-title').inner_text() == "등록된 페이지 (2개)"
        browser.close()

VIEWS = ["", "quick_run", "single_pipeline", "parallel_pipeline", "reports", "history", "team_new", "pages",
         "tc_studio"]
TITLE = """() => {
  const main = document.getElementById('main'), m = main.getBoundingClientRect();
  const t = [...main.querySelectorAll('.pipeline-title,.page-title,.ov-heading,.hist-heading')]
    .find((e) => e.getBoundingClientRect().height > 0);
  if (!t) return null;
  const r = t.getBoundingClientRect(), cs = getComputedStyle(t);
  return {x: Math.round(r.left - m.left), y: Math.round(r.top - m.top), size: cs.fontSize,
          font: cs.fontFamily.split(',')[0].replace(/["']/g, ''), visible: cs.webkitTextFillColor !== 'rgba(0, 0, 0, 0)',
          width: Math.round(main.firstElementChild.getBoundingClientRect().width)};
}"""


def test_every_view_starts_with_the_same_title_position_and_width(tmp_path):
    (tmp_path / "project" / "testcases").mkdir(parents=True)
    with dashboard_server(tmp_path / "project") as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.goto(base + "/")
        seen = {}
        for view in VIEWS:
            page.evaluate(f"selectView('{view}')")
            page.wait_for_function(f"({TITLE})() !== null", timeout=10000)
            page.wait_for_timeout(300)
            seen[view or "dashboard"] = page.evaluate(TITLE)
        browser.close()
    reference = seen["quick_run"]
    for name, got in seen.items():
        assert got["visible"], f"{name}: 제목 글자가 투명합니다"
        assert (got["x"], got["y"], got["size"], got["font"], got["width"]) == \
            (reference["x"], reference["y"], reference["size"], reference["font"], reference["width"]), (name, got, reference)
