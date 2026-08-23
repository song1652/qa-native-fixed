"""
자동 생성된 Playwright 테스트 코드
URL: https://www.saucedemo.com
케이스: tc_03_login_locked_user — 잠긴 계정 로그인 시 에러 메시지
"""
from playwright.sync_api import expect

BASE_URL = "https://www.saucedemo.com"


def test_login_locked_user(page):
    """잠긴 계정 로그인 시 에러 메시지 — locked_out_user 입력 시 잠금 에러 표시"""
    page.goto(BASE_URL)
    page.fill('[data-test="username"]', "locked_out_user")
    page.fill('[data-test="password"]', "secret_sauce")
    page.click('[data-test="login-button"]')
    expect(page.locator("div.error-message-container")).to_contain_text(
        "Epic sadface: Sorry, this user has been locked out."
    )
