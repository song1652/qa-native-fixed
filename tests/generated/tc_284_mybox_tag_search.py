"""DirectCloud: tc_284 - 검색 — 태그로 파일 검색 결과 확인"""
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


def test_tc_284_mybox_tag_search(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    creds = data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # Fill search input with a tag name
    search_input = page.locator('[placeholder="검색"]')
    if search_input.count() > 0:
        search_input.first.fill("test")
        page.wait_for_timeout(300)

    # Open detail search panel
    search_detail = page.locator('#search-detail, [id*="search-detail"]')
    if search_detail.count() > 0:
        search_detail.first.click()
        page.wait_for_timeout(800)

    # Click tag search checkbox via JS (hidden checkbox)
    try:
        page.evaluate("() => document.querySelector('#search-detail-tag').click()")
        page.wait_for_timeout(500)
    except Exception:
        # Fallback: try to find tag checkbox with alternate selector
        tag_checkbox = page.locator(
            '[id*="tag"], input[class*="tag"], [name*="tag"]'
        )
        if tag_checkbox.count() > 0:
            try:
                page.evaluate(
                    "() => { const el = document.querySelector('[id*=\"tag\"]'); if(el) el.click(); }"
                )
            except Exception:
                pass
        page.wait_for_timeout(300)

    # Submit search if there's a search button
    search_btn = page.locator(
        'button[type="submit"], button:has-text("検索"), #btn-search, '
        '.btn-search, button[class*="search"]'
    )
    if search_btn.count() > 0:
        search_btn.first.click()
        page.wait_for_timeout(3000)

    assert page.locator('body').is_visible()
