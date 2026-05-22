from pathlib import Path
from playwright.sync_api import expect

BASE_URL = "https://tweb.directcloud.jp/login"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_stay_signed_in_checkbox(page):
    page.goto(BASE_URL)
    page.wait_for_timeout(1000)

    checkbox = page.locator('[data-testid="persistent-session-checkbox"]')
    checkbox.wait_for(state="visible", timeout=10000)
    expect(checkbox).to_be_visible()

    initial_checked = checkbox.is_checked()
    assert initial_checked is True, "Checkbox should be checked by default"

    checkbox.click()
    page.wait_for_timeout(300)
    assert checkbox.is_checked() is False, "Checkbox should be unchecked after first click"

    checkbox.click()
    page.wait_for_timeout(300)
    assert checkbox.is_checked() is True, "Checkbox should be checked again after second click"
