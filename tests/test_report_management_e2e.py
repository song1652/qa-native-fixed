"""Real-browser coverage for the dashboard report-management workflow."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import unquote, urlparse

import pytest
from playwright.sync_api import Browser, Page, expect, sync_playwright


REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = REPO_ROOT / "agents" / "dashboard"
DESKTOP_SCREENSHOT = Path("/tmp/report-management-desktop.png")
MODAL_SCREENSHOT = Path("/tmp/report-management-modal.png")


def _load_dashboard_module() -> Any:
    for module_path in (str(REPO_ROOT / "scripts"), str(DASHBOARD_DIR)):
        if module_path not in sys.path:
            sys.path.insert(0, module_path)

    module_name = "serve_report_management_e2e"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(
        module_name, DASHBOARD_DIR / "serve.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@contextmanager
def _dashboard_server(serve: Any) -> Iterator[str]:
    server = serve.ReusableHTTPServer(("127.0.0.1", 0), serve.DashboardHandler)
    port = server.server_address[1]
    serve.ALLOWED_HOSTS = {f"127.0.0.1:{port}", f"localhost:{port}"}
    serve.ALLOWED_ORIGIN = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield serve.ALLOWED_ORIGIN
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _write_report(path: Path, heading: str, modified_at: int) -> None:
    path.write_text(
        f"<!doctype html><html><body><h1>{heading}</h1></body></html>",
        encoding="utf-8",
    )
    os.utime(path, (modified_at, modified_at))


@pytest.fixture(scope="module")
def report_browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=os.environ.get("HEADED") != "1"
        )
        yield browser
        browser.close()


@pytest.fixture
def report_page(report_browser: Browser) -> Iterator[Page]:
    context = report_browser.new_context(
        viewport={"width": 1280, "height": 900}
    )
    page = context.new_page()
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    try:
        yield page
    finally:
        context.close()
    assert not page_errors, (
        "JavaScript page errors: " + " | ".join(page_errors)
    )


@pytest.fixture
def report_dashboard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[str, Path, dict[str, str]]]:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    headings: dict[str, str] = {
        "preview-target.html": "Preview target",
        "keep-me.html": "Keep me",
        "특수 '인용\" <태그>&.html": "Quoted unicode report",
    }
    headings.update(
        {
            f"batch-{number:02d}.html": f"Batch {number:02d}"
            for number in range(22)
        }
    )
    for index, (name, heading) in enumerate(headings.items()):
        _write_report(reports_dir / name, heading, 1_700_000_000 + index)

    serve = _load_dashboard_module()
    monkeypatch.setattr(serve, "REPORTS_DIR", reports_dir)
    # Dashboard route/state modules import the path constant independently.
    # Patch those references too so this E2E server remains isolated from the
    # repository's real tests/reports directory.
    for module_name in ("_paths", "dash_state", "routes_get"):
        module = sys.modules.get(module_name)
        if module is not None and hasattr(module, "REPORTS_DIR"):
            monkeypatch.setattr(module, "REPORTS_DIR", reports_dir)
    with _dashboard_server(serve) as base_url:
        yield base_url, reports_dir, headings


def _open_reports(page: Page, base_url: str) -> None:
    page.goto(base_url, wait_until="domcontentloaded")
    page.locator("#tab-reports").click()
    expect(page.locator(".report-item").first).to_be_visible()


def _row(page: Page, name: str):
    return page.locator(".report-item").filter(
        has=page.get_by_text(name, exact=True)
    )


def _confirm_delete(page: Page, confirm: bool) -> None:
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible()
    label = "삭제" if confirm else "취소"
    dialog.get_by_role("button", name=label, exact=True).click()
    expect(dialog).to_be_hidden()


def _save_optional_screenshot(page: Page, test_name: str) -> None:
    artifact_dir = os.environ.get("REPORT_MANAGEMENT_E2E_ARTIFACT_DIR")
    if not artifact_dir:
        return
    destination = Path(artifact_dir)
    destination.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(destination / f"{test_name}.png"), full_page=True)


def _assert_desktop_layout(page: Page) -> None:
    layout = page.locator(".report-workspace")
    panels = layout.locator(".report-panel")
    expect(panels).to_have_count(2)
    expect(page.locator(".report-preview-empty")).to_be_visible()
    bounds = page.evaluate(
        """() => ({
          width: window.innerWidth,
          height: window.innerHeight,
          panels: [...document.querySelectorAll(
            '.report-workspace > .report-panel'
          )]
            .map(panel => {
              const box = panel.getBoundingClientRect();
              return {
                left: box.left, top: box.top,
                right: box.right, bottom: box.bottom,
              };
            }),
          empty: (() => {
            const empty = document.querySelector('.report-preview-empty');
            const box = empty.getBoundingClientRect();
            return {
              left: box.left, top: box.top,
              right: box.right, bottom: box.bottom,
            };
          })(),
        })"""
    )
    assert all(
        panel["left"] >= 0
        and panel["top"] >= 0
        and panel["right"] <= bounds["width"] + 1
        and panel["bottom"] <= bounds["height"] + 1
        for panel in bounds["panels"]
    ), bounds
    assert (
        bounds["empty"]["left"] >= 0
        and bounds["empty"]["top"] >= 0
        and bounds["empty"]["right"] <= bounds["width"] + 1
        and bounds["empty"]["bottom"] <= bounds["height"] + 1
    ), bounds


def test_single_delete_cancel_confirm_and_special_filename_actions(
    report_page: Page,
    report_dashboard: tuple[str, Path, dict[str, str]],
) -> None:
    base_url, reports_dir, _ = report_dashboard
    _open_reports(report_page, base_url)

    special_name = "특수 '인용\" <태그>&.html"
    search = report_page.get_by_role("textbox", name="리포트 검색")
    search.fill(special_name)
    special_row = _row(report_page, special_name)
    expect(special_row).to_have_count(1)
    expect(special_row).to_have_attribute("data-name", special_name)
    expect(
        report_page.get_by_role("checkbox", name=f"{special_name} 선택")
    ).to_be_visible()

    special_row.get_by_role("button", name=re.compile(r"열기$")).click()
    iframe_src = report_page.locator("#report-iframe").get_attribute("src")
    assert iframe_src is not None
    assert unquote(urlparse(iframe_src).path) == f"/reports/{special_name}"
    expect(
        report_page.frame_locator("#report-iframe").get_by_role(
            "heading", name="Quoted unicode report"
        )
    ).to_be_visible()

    with report_page.expect_popup() as popup_info:
        special_row.get_by_role("link", name=re.compile(r"새 탭$")).click()
    popup = popup_info.value
    expect(
        popup.get_by_role("heading", name="Quoted unicode report")
    ).to_be_visible()
    assert unquote(urlparse(popup.url).path) == f"/reports/{special_name}"
    popup.close()

    target_name = "preview-target.html"
    search.fill(target_name)
    target_row = _row(report_page, target_name)
    target_row.get_by_role("button", name=re.compile(r"열기$")).click()
    expect(
        report_page.frame_locator("#report-iframe").get_by_role(
            "heading", name="Preview target"
        )
    ).to_be_visible()
    report_page.screenshot(path=str(DESKTOP_SCREENSHOT), full_page=True)
    _save_optional_screenshot(report_page, "test_report_management_success")

    target_row.get_by_role("button", name=re.compile(r"삭제$")).click()
    report_page.screenshot(path=str(MODAL_SCREENSHOT), full_page=True)
    _confirm_delete(report_page, confirm=False)
    expect(_row(report_page, target_name)).to_be_visible()
    assert (reports_dir / target_name).exists()

    _row(report_page, target_name).get_by_role(
        "button", name=re.compile(r"삭제$")
    ).click()
    _confirm_delete(report_page, confirm=True)
    expect(_row(report_page, target_name)).to_have_count(0)
    expect(report_page.locator("#report-iframe")).to_have_count(0)
    assert not (reports_dir / target_name).exists()


def test_filter_sort_select_all_across_pages_and_bulk_delete(
    report_page: Page,
    report_dashboard: tuple[str, Path, dict[str, str]],
) -> None:
    base_url, reports_dir, headings = report_dashboard
    _open_reports(report_page, base_url)
    _assert_desktop_layout(report_page)

    sort = report_page.get_by_role("combobox", name="리포트 정렬")
    sort.select_option("oldest")
    expect(report_page.locator(".report-item").first).to_have_attribute(
        "data-name", "preview-target.html"
    )
    sort.select_option("newest")
    expect(report_page.locator(".report-item").first).to_have_attribute(
        "data-name", "batch-21.html"
    )
    sort.select_option("name")
    expected_first = sorted(headings, key=str.casefold)[0]
    expect(report_page.locator(".report-item").first).to_have_attribute(
        "data-name", expected_first
    )

    search = report_page.get_by_role("textbox", name="리포트 검색")
    search_handle = search.element_handle()
    assert search_handle is not None
    search_handle.evaluate(
        """input => {
          input.focus();
          input.dispatchEvent(new CompositionEvent(
            'compositionstart', { bubbles: true }
          ));
          input.value = 'batch-';
          input.dispatchEvent(new InputEvent('input', {
            bubbles: true,
            data: '-',
            inputType: 'insertCompositionText',
            isComposing: true,
          }));
        }"""
    )
    assert search_handle.evaluate(
        "input => input === document.getElementById('report-search-input')"
    )
    expect(search).to_have_value("batch-")
    search_handle.evaluate(
        "input => input.dispatchEvent(new CompositionEvent('compositionend', "
        "{ bubbles: true, data: 'batch-' }))"
    )
    # Complete the same value through Playwright's trusted input path;
    # compositionend itself is browser/IME controlled and may not mutate
    # the value in synthetic WebKit/Chromium events.
    search.fill("batch-")
    expect(report_page.locator(".report-item")).to_have_count(20)
    expect(search).to_be_focused()
    expect(report_page.locator(".report-pager")).to_be_visible()

    select_all = report_page.get_by_role("checkbox", name="검색 결과 전체 선택")
    select_all.check()
    expect(report_page.locator(".report-selection-count")).to_contain_text(
        "22"
    )

    pager = report_page.locator(".report-pager")
    pager.get_by_role("button").last.click()
    expect(pager).to_contain_text("2 / 2")
    expect(report_page.locator(".report-item")).to_have_count(2)
    for number in (20, 21):
        expect(
            report_page.get_by_role(
                "checkbox", name=f"batch-{number:02d}.html 선택"
            )
        ).to_be_checked()

    report_page.get_by_role("button", name="선택 삭제", exact=True).click()
    _confirm_delete(report_page, confirm=False)
    expect(report_page.locator(".report-selection-count")).to_contain_text(
        "22"
    )
    remaining = sum(
        (reports_dir / f"batch-{number:02d}.html").exists()
        for number in range(22)
    )
    assert remaining == 22

    report_page.get_by_role("button", name="선택 삭제", exact=True).click()
    _confirm_delete(report_page, confirm=True)
    expect(report_page.locator(".report-item")).to_have_count(0)
    assert not any(reports_dir.glob("batch-*.html"))

    search.fill("")
    expect(_row(report_page, "keep-me.html")).to_be_visible()
    search.fill("no-report-can-match-this")
    expect(report_page.locator(".report-item")).to_have_count(0)


def test_delete_error_preserves_selection_and_refresh_loads_new_report(
    report_page: Page,
    report_dashboard: tuple[str, Path, dict[str, str]],
) -> None:
    base_url, reports_dir, _ = report_dashboard
    _open_reports(report_page, base_url)

    name = "keep-me.html"
    report_page.get_by_role("textbox", name="리포트 검색").fill(name)
    checkbox = report_page.get_by_role("checkbox", name=f"{name} 선택")
    checkbox.check()
    expect(report_page.locator(".report-selection-count")).to_contain_text("1")

    def fail_delete(route) -> None:
        route.fulfill(
            status=500,
            content_type="application/json",
            body=json.dumps(
                {"ok": False, "error": "의도한 삭제 실패"},
                ensure_ascii=False,
            ),
        )

    report_page.route("**/api/reports/delete", fail_delete)
    report_page.get_by_role("button", name="선택 삭제", exact=True).click()
    _confirm_delete(report_page, confirm=True)
    expect(_row(report_page, name)).to_be_visible()
    expect(
        report_page.get_by_role("checkbox", name=f"{name} 선택")
    ).to_be_checked()
    expect(report_page.locator(".report-selection-count")).to_contain_text("1")
    expect(report_page.locator("#toast-container")).to_contain_text(
        "의도한 삭제 실패"
    )
    assert (reports_dir / name).exists()
    report_page.unroute("**/api/reports/delete", fail_delete)

    refreshed_name = "refresh-added.html"
    _write_report(
        reports_dir / refreshed_name, "Added before refresh", 1_800_000_000
    )
    report_page.get_by_role("button", name="새로고침", exact=True).click()
    expect(_row(report_page, refreshed_name)).to_have_count(0)
    expect(
        report_page.get_by_role("checkbox", name=f"{name} 선택")
    ).to_be_checked()
    expect(report_page.locator(".report-selection-count")).to_contain_text("1")
    report_page.get_by_role("textbox", name="리포트 검색").fill("")
    expect(_row(report_page, refreshed_name)).to_be_visible()
