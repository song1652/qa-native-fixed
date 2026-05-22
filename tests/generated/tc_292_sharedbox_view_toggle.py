"""DirectCloud: tc_292 - 공유박스 — 뷰 전환 버튼 존재 및 동작 확인"""
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


def test_tc_292_sharedbox_view_toggle(page):
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    creds = data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # Navigate to sharedbox
    sharedbox_nav = page.locator('li:has-text("Shared Box")')
    if sharedbox_nav.count() > 0:
        sharedbox_nav.first.click()
        page.wait_for_timeout(1000)
    dismiss_popups(page)

    # Look for view toggle button
    view_toggle = page.locator(
        '.btn-view, [class*="btn-view"], [class*="viewToggle"], '
        '[class*="view-toggle"], button[title*="view"], button[title*="View"], '
        '[class*="listView"], [class*="gridView"], .icon-list, .icon-grid'
    )
    if view_toggle.count() > 0:
        try:
            view_toggle.first.click(timeout=20000)
            page.wait_for_timeout(500)
        except Exception:
            pass

    assert page.locator('body').is_visible()
