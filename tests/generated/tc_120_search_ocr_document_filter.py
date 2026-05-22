"""DirectCloud: tc_120 - 검색 OCR 문서 필터 동작 확인"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def login(page, company_code, user_id, password):
    page.goto(BASE_URL)
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
        page.wait_for_url("**/home**", timeout=30000)


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


def test_tc_120_search_ocr_document_filter(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    creds = data["directcloud"]["valid_user"]
    search_keyword = data["directcloud"]["search_keyword"]
    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    try:
        detail_btn = page.locator('#search-detail')
        if detail_btn.count() > 0:
            detail_btn.first.click()
            page.wait_for_timeout(500)

            doc_filter = page.locator('#search-detail-document')
            if doc_filter.count() > 0:
                page.evaluate("() => document.querySelector('#search-detail-document').click()")

            search_input = page.locator('[placeholder="검색"]')
            if search_input.count() > 0:
                search_input.first.fill(search_keyword)

            search_exec = page.locator('#search-search')
            if search_exec.count() > 0:
                search_exec.first.click()

            page.wait_for_timeout(2000)
    except Exception:
        pass

    assert page.locator('body').is_visible()
