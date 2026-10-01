"""모든 대시보드 화면은 같은 배치로 시작한다 — 제목 위치·크기·글꼴과 본문 폭.

화면마다 가운데 박스·다른 여백·다른 제목 크기를 쓰면 탭을 옮길 때 제목이 튄다(2026-10-01 정리).
새 화면을 추가하면 VIEWS에 넣는다.
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from tests.unit.import_studio.import_studio_test_support import dashboard_server  # noqa: E402

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
