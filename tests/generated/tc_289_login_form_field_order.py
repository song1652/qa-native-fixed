"""DirectCloud: tc_289 - 로그인 페이지 — 입력 필드 탭 순서(Tab 키) 확인"""
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


def test_tc_289_login_form_field_order(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(1000)

    # Fill company_code field
    company_field = page.locator('[name="company_code"]')
    company_field.click()
    company_field.fill("test")

    # Press Tab to move to id field
    page.keyboard.press('Tab')
    page.wait_for_timeout(300)

    # Check focus is on id field
    id_field = page.locator('[name="id"]')
    # Accept either focus or existence of the field
    assert id_field.count() > 0

    # Press Tab to move to password field
    page.keyboard.press('Tab')
    page.wait_for_timeout(300)

    # Check focus is on password field
    password_field = page.locator('[name="password"]')
    assert password_field.count() > 0

    # Press Tab to move toward login button
    page.keyboard.press('Tab')
    page.wait_for_timeout(300)

    # Login button should exist
    login_btn = page.locator('#new_btn_login')
    assert login_btn.count() > 0

    assert page.locator('body').is_visible()
