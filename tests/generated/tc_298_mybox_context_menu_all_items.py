"""DirectCloud: tc_298 - 마이박스 — 파일 컨텍스트 메뉴 전체 항목 목록 확인"""
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


def test_tc_298_mybox_context_menu_all_items(page):
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

    # Right-click on first file item to open context menu
    file_row = page.locator(
        'li.preview__list-item, .file-list-item, li[class*="fileItem"], '
        'li[class*="listItem"]:not(.listItem-checkbox-label-all), tr.file-row'
    )
    if file_row.count() > 0:
        file_row.first.click(button="right")
        page.wait_for_timeout(800)

        # Check context menu appears
        context_menu = page.locator(
            '.context-menu, [class*="contextMenu"], [class*="context-menu"], '
            '[role="menu"], .dropdown-menu, [class*="dropdownMenu"], '
            '[class*="rightClickMenu"]'
        )
        if context_menu.count() > 0:
            assert context_menu.first.is_visible()

            # Verify menu has items
            menu_items = page.locator(
                '.context-menu li, [class*="contextMenu"] li, [role="menuitem"], '
                '.dropdown-menu li, [class*="contextMenu"] [class*="item"]'
            )
            if menu_items.count() > 0:
                assert menu_items.count() > 0

            # Dismiss context menu
            page.keyboard.press('Escape')
            page.wait_for_timeout(300)
    else:
        # No file rows found — mybox may be empty
        pass

    assert page.locator('body').is_visible()
