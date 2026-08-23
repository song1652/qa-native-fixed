"""
자동 생성된 Playwright 테스트 코드
URL: https://www.saucedemo.com
케이스: tc_02_login_invalid_password — 잘못된 비밀번호 로그인 실패
"""
from playwright.sync_api import expect

BASE_URL = "https://www.saucedemo.com"


def test_login_invalid_password(page):
    """잘못된 비밀번호 로그인 실패 — 에러 메시지 표시 확인"""
    page.goto(BASE_URL)
    page.fill('[data-test="username"]', "standard_user")
    page.fill('[data-test="password"]', "wrong_password")
    page.click('[data-test="login-button"]')
    expect(page.locator("div.error-message-container")).to_contain_text(
        "Epic sadface: Username and password do not match any user in this service"
    )
