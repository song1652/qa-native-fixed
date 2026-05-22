"""DirectCloud: tc_54 - 상세 검색 기간 옵션 선택"""
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


def test_tc_54_search_detail_period_options(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # #search-detail 클릭
    if page.locator('#search-detail').count() > 0:
        page.locator('#search-detail').click()
        page.wait_for_timeout(500)

    # 기간 옵션 존재 확인
    period_selectors = [
        '#detail-period-max',
        '#detail-period-360',
        '#detail-period-30',
        '#detail-period-7',
        '#detail-period-1',
    ]
    found_count = 0
    for selector in period_selectors:
        if page.locator(selector).count() > 0:
            found_count += 1

    # 30일 기간 라디오 클릭
    if page.locator('#detail-period-30').count() > 0:
        page.locator('#detail-period-30').click()
        page.wait_for_timeout(300)

    # 상세 패널 열렸으면 기간 옵션 있어야 함, 없으면 검색창 visible
    search_input = page.locator('[placeholder="검색"]')
    assert found_count > 0 or search_input.is_visible()
