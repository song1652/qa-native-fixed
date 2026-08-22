"""
tc_03_login_locked_user.py
URL: https://www.saucedemo.com
케이스: 잠긴 계정(locked_out_user)으로 로그인 시 에러에 'locked out' 포함 검증
"""
import json
from pathlib import Path
from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = _ROOT / "config" / "test_data.json"


def test_login_locked_user(page: Page):
    """locked_out_user 계정 로그인 시 'locked out' 에러 메시지 검증"""
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    sd = data["saucedemo"]

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    page.locator('[data-test="username"]').fill(sd["locked_user"])
    page.locator('[data-test="password"]').fill(sd["valid_password"])
    page.locator('[data-test="login-button"]').click()

    error = page.locator('[data-test="error"]')
    expect(error).to_be_visible()
    expect(error).to_contain_text("locked out")
