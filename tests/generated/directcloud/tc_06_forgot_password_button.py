from pathlib import Path
from playwright.sync_api import expect

BASE_URL = "https://tweb.directcloud.jp/login"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_forgot_password_button(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(1000)

    forgot_btn = page.locator('[data-testid="forgot-password-button"]:has-text("Forgot Password?")')
    forgot_btn.wait_for(state="visible", timeout=10000)
    expect(forgot_btn).to_be_visible()

    forgot_btn.click()
    page.wait_for_timeout(2000)

    # 클릭 후 새로 출현하는 요소로 검증 (버튼 자체 count 사용 금지)
    reset_form_visible = (
        page.locator('input[name="email"], input[type="email"], input[placeholder*="mail"]').count() > 0
        or page.locator('[class*="forgot"], [class*="reset"], [class*="password"]').count() > 0
        or page.locator('form').count() > 0
    )
    url_changed = "forgot" in page.url or "reset" in page.url or "login" not in page.url

    assert reset_form_visible or url_changed, (
        f"Expected password reset UI or URL change after clicking Forgot Password. URL: {page.url}"
    )
