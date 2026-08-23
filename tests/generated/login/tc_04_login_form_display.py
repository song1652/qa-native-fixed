"""
자동 생성된 Playwright 테스트 코드
URL: https://www.saucedemo.com
케이스: tc_04_login_form_display — 로그인 폼 UI 요소 표시 확인
"""
from playwright.sync_api import expect

BASE_URL = "https://www.saucedemo.com"


def test_login_form_display(page):
    """로그인 폼 UI 요소 표시 확인 — 로고, username/password 입력, Login 버튼 가시성 확인"""
    page.goto(BASE_URL)
    expect(page.locator(".login_logo")).to_contain_text("Swag Labs")
    expect(page.locator('[data-test="username"]')).to_be_visible()
    expect(page.locator('[data-test="password"]')).to_be_visible()
    expect(page.locator('[data-test="login-button"]')).to_be_visible()
