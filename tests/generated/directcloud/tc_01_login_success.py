import json
import re
from pathlib import Path

BASE_URL = "https://tweb.directcloud.jp/login"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_login_success(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))["directcloud"]["valid_user"]

    page.goto(BASE_URL)
    page.wait_for_timeout(1000)
    page.fill('[name="company_code"]', data["company"])
    page.fill('[name="id"]', data["username"])
    page.fill('[name="password"]', data["password"])

    btn = page.locator("#new_btn_login")
    btn.wait_for(state="visible", timeout=10000)
    btn.click()

    # tweb 환경은 로그인 후 /home 또는 /mybox 로 이동
    try:
        page.wait_for_url(re.compile(r"/(home|mybox|recents)"), timeout=20000)
    except Exception:
        page.goto(BASE_URL)
        page.wait_for_timeout(3000)
        page.fill('[name="company_code"]', data["company"])
        page.fill('[name="id"]', data["username"])
        page.fill('[name="password"]', data["password"])
        page.locator("#new_btn_login").click()
        page.wait_for_url(re.compile(r"/(home|mybox|recents)"), timeout=30000)

    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception:
        pass

    assert "login" not in page.url, f"Should have left login page, got: {page.url}"
    assert any(p in page.url for p in ["/home", "/mybox", "/recents"]), (
        f"Expected home/mybox/recents after login, got: {page.url}"
    )
