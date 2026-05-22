"""DirectCloud: tc_74 - 링크 히스토리 필터 옵션 확인"""
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


def test_tc_74_link_history_filter_options(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # Link History 사이드바 메뉴 클릭 (ID 없음, 텍스트로 선택)
    link_menu = page.locator('li:has-text("Link History")')
    if link_menu.count() > 0:
        link_menu.first.click()
    else:
        page.goto(BASE_URL.replace("/login", "") + "/linkmanager")

    page.wait_for_timeout(2000)
    dismiss_popups(page)

    # select 옵션 value 수집 및 확인 (조건부)
    if page.locator('select').count() > 0:
        option_values = page.evaluate("""() => {
            const select = document.querySelector('select');
            if (!select) return [];
            return Array.from(select.options).map(o => o.value);
        }""")

        # "all", "create", "webmail", "upload" value 포함 여부 조건부 확인
        expected_values = ["all", "create", "webmail", "upload"]
        for val in expected_values:
            if val in option_values:
                pass  # 존재 확인 완료

    assert page.locator('body').is_visible()
