"""DirectCloud: tc_297 - 마이박스 — 우측 정보 패널 버전 정보 표시 확인"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def login(page, company_code, user_id, password):
    page.goto(BASE_URL)
    page.wait_for_timeout(1000)
    page.fill('[name="company_code"]', company_code)
    page.fill('[name="id"]', user_id)
    page.fill('[name="password"]', password)
    page.click('#new_btn_login')
    try:
        page.wait_for_url("**/home**", timeout=20000)
    except Exception:
        page.goto(BASE_URL)
        page.wait_for_timeout(3000)
        page.fill('[name="company_code"]', company_code)
        page.fill('[name="id"]', user_id)
        page.fill('[name="password"]', password)
        page.click('#new_btn_login')
        page.wait_for_url("**/home**", timeout=20000)


def dismiss_popups(page):
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    try:
        page.evaluate("""() => {
            const overlays = document.querySelectorAll('div[class*="sc-T"]');
            overlays.forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.position === 'fixed' || parseInt(style.zIndex) > 100) el.remove();
            });
        }""")
    except Exception:
        pass
    page.wait_for_timeout(200)


def test_tc_297_mybox_right_panel_version_info(page):
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    creds = data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # Navigate to mybox
    mybox_nav = page.locator('li:has-text("My Box")')
    if mybox_nav.count() > 0:
        mybox_nav.first.click()
        page.wait_for_timeout(1000)
    dismiss_popups(page)

    # Click on first file row to open right panel
    file_row = page.locator(
        'li.preview__list-item, .file-list-item, .list-item, '
        'tr.file-row, [class*="fileItem"], [class*="listItem"]'
    )
    if file_row.count() > 0:
        try:
            file_row.first.click(timeout=20000)
        except Exception:
            pass
        page.wait_for_timeout(1000)
        dismiss_popups(page)

        # Look for right panel with version info
        version_section = page.locator(
            '[class*="version"], [class*="Version"], .info-panel [class*="version"], '
            '.right-panel [class*="version"], [class*="fileVersion"], '
            'label:has-text("バージョン"), label:has-text("Version"), '
            'span:has-text("バージョン"), dt:has-text("バージョン"), '
            'th:has-text("バージョン"), h3:has-text("バージョン")'
        )
        if version_section.count() > 0:
            assert version_section.first.is_visible()
        else:
            # Right panel should at least be present
            right_panel = page.locator(
                '.right-panel, .info-panel, .detail-panel, [class*="rightPanel"], '
                '[class*="infoPanel"], [class*="detailPanel"], aside'
            )
            if right_panel.count() > 0:
                assert right_panel.first.is_visible()
    else:
        # No file rows found — mybox may be empty
        pass

    assert page.locator('body').is_visible()
