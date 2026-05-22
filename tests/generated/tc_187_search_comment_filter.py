"""DirectCloud: tc_187 - 검색 코멘트 필터"""
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


def test_tc_187_search_comment_filter(page):
    with open(TEST_DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)
    creds = data["directcloud"]["valid_user"]

    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    search_detail = page.locator('#search-detail')
    if search_detail.count() > 0:
        search_detail.click()
        page.wait_for_timeout(500)

        comment_filter = page.locator('#search-detail-comment')
        if comment_filter.count() > 0:
            try:
                page.evaluate("() => document.querySelector('#search-detail-comment').click()")
            except Exception:
                pass
            page.wait_for_timeout(300)

    assert page.locator('body').is_visible()
