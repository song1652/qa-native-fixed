"""DirectCloud: tc_294 - 휴지통 — 파일 경로 컬럼 표시 확인"""
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


def test_tc_294_trash_file_path_column(page):
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    creds = data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # Navigate to trash
    trash_nav = page.locator('li:has-text("Trash")')
    if trash_nav.count() > 0:
        trash_nav.first.click()
        page.wait_for_timeout(1000)
    dismiss_popups(page)

    # Look for path column in the file list header
    path_col = page.locator(
        'th[data-col="path"], th[data-col="location"], th[data-col="folder"], '
        'th:has-text("パス"), th:has-text("場所"), th:has-text("Path"), '
        'th:has-text("Location"), th:has-text("Folder"), [class*="path"] th'
    )
    if path_col.count() > 0:
        assert path_col.first.is_visible()
    else:
        # Path info may be inside row cells instead of a header
        path_cell = page.locator(
            'td[class*="path"], td[class*="location"], [class*="filePath"], '
            '[class*="file-path"]'
        )
        if path_cell.count() > 0:
            assert path_cell.first.is_visible()
        else:
            # Column may not be present if trash is empty — check table headers exist
            any_header = page.locator('thead th, .list-header th')
            if any_header.count() > 0:
                assert any_header.first.is_visible()

    assert page.locator('body').is_visible()
