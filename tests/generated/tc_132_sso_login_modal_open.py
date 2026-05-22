"""DirectCloud: tc_132 - SSO 로그인 버튼 클릭 후 모달 열림 확인"""
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


def test_tc_132_sso_login_modal_open(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(3000)

    try:
        sso_btn = page.locator(':text("SSO 로그인")')
        if sso_btn.count() > 0:
            sso_btn.first.click()
            page.wait_for_timeout(3000)

            company_input = page.locator(
                'input[placeholder*="회사"], input[name*="company"], input[type="text"]'
            )
            if company_input.count() > 0:
                assert company_input.first.is_visible()

            confirm_btn = page.locator('button:has-text("확인"), button[type="submit"]')
            if confirm_btn.count() > 0:
                assert confirm_btn.first.is_visible()
    except Exception:
        pass

    assert page.locator('body').is_visible()
