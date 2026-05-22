"""DirectCloud: tc_90 - Stay signed in 체크 해제 후 로그인 성공 확인"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_tc_90_login_stay_signed_in_affects_login(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]

    page.goto(BASE_URL)
    page.wait_for_load_state('domcontentloaded')

    # Stay signed in 체크박스 해제 시도
    checkbox = page.locator('input[type="checkbox"]')
    if checkbox.count() > 0:
        try:
            if checkbox.first.is_checked():
                checkbox.first.click()
                page.wait_for_timeout(300)
        except Exception:
            pass

    page.fill('[name="company_code"]', user["company"])
    page.fill('[name="id"]', user["username"])
    page.fill('[name="password"]', user["password"])
    page.click('#new_btn_login')

    try:
        page.wait_for_url("**/home**", timeout=20000)
    except Exception:
        page.wait_for_timeout(3000)

    assert "mybox" in page.url or page.locator('[name="company_code"]').count() == 0
