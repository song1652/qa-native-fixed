import json
from pathlib import Path

BASE_URL = "https://tweb.directcloud.jp/login"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_login_wrong_company_code(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))["directcloud"]
    wrong = data["wrong_company"]
    valid = data["valid_user"]

    page.goto(BASE_URL)
    page.wait_for_timeout(1000)
    page.fill('[name="company_code"]', wrong["company"])
    page.fill('[name="id"]', valid["username"])
    page.fill('[name="password"]', valid["password"])

    btn = page.locator("#new_btn_login")
    btn.wait_for(state="visible", timeout=10000)
    btn.click()

    page.wait_for_timeout(5000)

    assert "mybox" not in page.url, f"Should not have navigated to mybox with wrong company code, got: {page.url}"
    assert "login" in page.url, f"Expected to stay on login page, got: {page.url}"
