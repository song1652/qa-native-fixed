"""
tc_02_login_invalid_password.py
URL: https://www.saucedemo.com
케이스: 잘못된 비밀번호로 로그인 시도 시 에러 메시지 표시 검증
"""
import json
from pathlib import Path
from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = _ROOT / "config" / "test_data.json"

_INVALID_PW_MSG = (
    "Epic sadface: Username and password do not match"
    " any user in this service"
)


def test_login_invalid_password(page: Page):
    """잘못된 비밀번호 로그인 시 에러 메시지 표시 검증"""
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    sd = data["saucedemo"]

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    page.locator('[data-test="username"]').fill(sd["valid_user"])
    page.locator('[data-test="password"]').fill(sd["invalid_password"])
    page.locator('[data-test="login-button"]').click()

    error = page.locator('[data-test="error"]')
    expect(error).to_be_visible()
    expect(error).to_contain_text(_INVALID_PW_MSG)
