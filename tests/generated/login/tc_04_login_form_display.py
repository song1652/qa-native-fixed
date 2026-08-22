"""
tc_04_login_form_display.py
URL: https://www.saucedemo.com
케이스: 로그인 폼 요소 표시 확인 (UI 표시 테스트)
"""
from pathlib import Path
from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = _ROOT / "config" / "test_data.json"


def test_login_form_display(page: Page):
    """로그인 폼 요소 visible 및 타이틀 'Swag Labs' 검증"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    expect(page).to_have_title("Swag Labs")
    expect(page.locator('[data-test="username"]')).to_be_visible()
    expect(page.locator('[data-test="password"]')).to_be_visible()
    expect(page.locator('[data-test="login-button"]')).to_be_visible()
