"""
tc_01_login_success.py
URL: https://www.saucedemo.com
케이스: standard_user로 정상 로그인 성공 후 인벤토리 페이지 이동 검증
"""
import json
import re
from pathlib import Path
from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = _ROOT / "config" / "test_data.json"


def test_login_success(page: Page):
    """standard_user 로 로그인 성공 시 /inventory.html 이동 검증"""
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    sd = data["saucedemo"]

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    page.locator('[data-test="username"]').fill(sd["valid_user"])
    page.locator('[data-test="password"]').fill(sd["valid_password"])
    page.locator('[data-test="login-button"]').click()

    expect(page).to_have_url(re.compile(r"/inventory"))
