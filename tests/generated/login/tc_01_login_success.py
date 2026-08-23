"""
자동 생성된 Playwright 테스트 코드
URL: https://www.saucedemo.com
케이스: tc_01_login_success — 정상 로그인 성공
"""
import re
from playwright.sync_api import expect

BASE_URL = "https://www.saucedemo.com"


def test_login_success(page):
    """정상 로그인 성공 — standard_user/secret_sauce 입력 후 /inventory.html 이동 확인"""
    page.goto(BASE_URL)
    page.fill('[data-test="username"]', "standard_user")
    page.fill('[data-test="password"]', "secret_sauce")
    page.click('[data-test="login-button"]')
    expect(page).to_have_url(re.compile(r"/inventory\.html"))
