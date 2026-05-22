"""DirectCloud: tc_275 - 잘못된 회사코드로 로그인 실패 확인"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_tc_275_login_wrong_company_code(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    wrong = data["directcloud"]["wrong_company"]
    valid = data["directcloud"]["valid_user"]

    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')

    # 잘못된 회사코드 + 유효한 계정으로 로그인 시도
    page.fill('[name="company_code"]', wrong["company"])
    page.fill('[name="id"]', valid["username"])
    page.fill('[name="password"]', valid["password"])
    page.click('#new_btn_login')
    page.wait_for_timeout(3000)

    # 로그인 실패 확인 - 로그인 페이지 유지
    current_url = page.url
    assert "login" in current_url or "mybox" not in current_url
    assert page.locator('#new_btn_login').count() > 0
