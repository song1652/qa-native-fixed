from pathlib import Path

BASE_URL = "https://tweb.directcloud.jp/login"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_login_empty_fields(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(1000)

    btn = page.locator("#new_btn_login")
    btn.wait_for(state="visible", timeout=10000)
    btn.click()

    page.wait_for_timeout(3000)

    assert "login" in page.url, f"Expected to stay on login page, got: {page.url}"
    assert "mybox" not in page.url, f"Should not have navigated to mybox, got: {page.url}"
    page.locator('[name="company_code"]').wait_for(state="visible", timeout=5000)
