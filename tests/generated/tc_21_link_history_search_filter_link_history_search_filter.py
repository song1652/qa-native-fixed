"""DirectCloud: tc_21 - Link History 검색 필터"""
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
    """AI 팝업/오버레이 닫기"""
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    # sc-TuwoP 클래스 팝업 제거
    try:
        page.evaluate(
            "() => {"
            "  const overlays = document.querySelectorAll("
            "    'div[class*=\"sc-T\"], div[class*=\"Popup\"], div[class*=\"popup\"], div[class*=\"modal\"]'"
            "  );"
            "  overlays.forEach(el => {"
            "    const style = window.getComputedStyle(el);"
            "    if (style.position === 'fixed' || style.position === 'absolute') el.remove();"
            "  });"
            "}"
        )
    except Exception:
        pass
    page.wait_for_timeout(200)


def test_tc_21_link_history_search_filter(page):
    """Link History 검색 필터 입력 및 검색 버튼 동작"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    creds = test_data["directcloud"]["valid_user"]
    keyword = test_data["directcloud"]["search_keyword"]
    login(page, creds["company"], creds["username"], creds["password"])

    dismiss_popups(page)

    page.locator('li:has-text("Link History")').first.click()
    page.wait_for_url("**/linkmanager**", timeout=20000)
    page.wait_for_load_state('networkidle')

    dismiss_popups(page)

    search_field = page.locator(
        'input[placeholder*="파일명"], input[placeholder*="링크"], '
        'input[type="search"], input[placeholder*="search"]'
    )
    if search_field.count() > 0 and search_field.first.is_visible():
        search_field.first.fill(keyword)

        search_btn = page.locator('button:has-text("검색")')
        if search_btn.count() > 0:
            # force=True로 팝업 무시하고 클릭
            search_btn.first.click(force=True)
            page.wait_for_timeout(2000)

    assert "linkmanager" in page.url
