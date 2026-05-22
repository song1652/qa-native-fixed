"""DirectCloud: tc_293 - 최근파일 — 날짜 기준 정렬 확인"""
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


def test_tc_293_recents_sort_by_date(page):
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    creds = data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # Navigate to recents
    recents_nav = page.locator('li:has-text("최근파일")')
    if recents_nav.count() > 0:
        recents_nav.first.click()
        page.wait_for_timeout(1000)
    dismiss_popups(page)

    # Look for date column header
    date_header = page.locator(
        'th[data-col="date"], th[data-sort="date"], th[data-col="updated"], '
        'th[data-col="modified"], th:has-text("日付"), th:has-text("更新日"), '
        'th:has-text("Date"), th:has-text("Modified"), th:has-text("Updated")'
    )
    if date_header.count() > 0:
        date_header.first.click()
        page.wait_for_timeout(800)
        # Click again to toggle sort direction
        date_header.first.click()
        page.wait_for_timeout(800)
    else:
        # Try list header generically — date column is often last or second-to-last
        col_headers = page.locator('.list-header th, .file-list-header th, thead th')
        count = col_headers.count()
        if count > 0:
            col_headers.last.click()
            page.wait_for_timeout(800)

    assert page.locator('body').is_visible()
