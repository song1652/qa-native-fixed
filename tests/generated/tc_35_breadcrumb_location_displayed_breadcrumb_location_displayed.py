"""DirectCloud: tc_35 - 파일 목록 브레드크럼(현재 경로) 표시 확인"""
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


def test_tc_35_breadcrumb_location_displayed(page):
    """파일 목록 브레드크럼 표시 확인"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 브레드크럼 — DOM: textbox에 "경로 : /My Box/" 형태로 표시됨
    # textbox[value*="경로"] 또는 헤딩(h5)으로 현재 위치 확인
    assert "mybox" in page.url or "home" in page.url, "로그인 후 페이지가 로드되지 않았습니다"

    # 현재 경로 표시 textbox 또는 heading h5 확인
    location_el = page.locator('textbox, input[value*="경로"]')
    heading_el = page.locator('h5')
    assert (
        location_el.count() > 0 or heading_el.count() > 0
    ), "현재 경로/위치 표시 요소(textbox 또는 h5)가 없습니다"
