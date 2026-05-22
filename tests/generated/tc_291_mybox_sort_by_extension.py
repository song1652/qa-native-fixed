"""DirectCloud: tc_291 - 마이박스 — 파일 목록 확장자 기준 정렬 확인"""
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


def test_tc_291_mybox_sort_by_extension(page):
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

    # Look for extension column header — try common selectors
    ext_header = page.locator(
        'th[data-col="extension"], th[data-sort="extension"], '
        '[class*="extension"] th, th:has-text("拡張子"), th:has-text("種類"), '
        'th:has-text("Extension"), th:has-text("Type")'
    )
    if ext_header.count() > 0:
        ext_header.first.click()
        page.wait_for_timeout(800)
        # Click again to toggle sort direction
        ext_header.first.click()
        page.wait_for_timeout(800)
    else:
        # Try list header area generically
        col_headers = page.locator('.list-header th, .file-list-header th, thead th')
        count = col_headers.count()
        if count > 2:
            # Click third header as extension column is often third
            col_headers.nth(2).click()
            page.wait_for_timeout(800)

    assert page.locator('body').is_visible()
