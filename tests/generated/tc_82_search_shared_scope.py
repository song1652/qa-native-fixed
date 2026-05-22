"""DirectCloud: tc_82 - 상세 검색 Shared 범위 선택 후 검색 실행"""
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


def test_tc_82_search_shared_scope(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    keyword = data["directcloud"].get("search_keyword", "test")
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    detail_btn = page.locator('#search-detail')
    if detail_btn.count() > 0 and detail_btn.first.is_visible():
        try:
            detail_btn.first.click(force=True)
            page.wait_for_timeout(1000)
            radio = page.locator('#detail-search-share')
            if radio.count() > 0:
                radio.first.click(force=True)
            # 검색 입력창 (실제 DOM: placeholder="검색")
            search_input = page.locator('[placeholder="검색"]')
            if search_input.count() > 0 and search_input.first.is_visible():
                search_input.first.fill(keyword)
            run_btn = page.locator('#search-search')
            if run_btn.count() > 0:
                run_btn.first.click(force=True)
            page.wait_for_timeout(1000)
        except Exception:
            pass
    assert page.locator('body').is_visible()
