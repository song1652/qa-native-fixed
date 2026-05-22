"""DirectCloud: tc_246 - 로그인 모든 필드 비운 채 로그인 버튼 클릭 확인"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_tc_246_login_empty_all_fields(page):
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')

    # 모든 필드 비운 채 로그인 버튼 클릭
    page.click('#new_btn_login')
    page.wait_for_timeout(2000)

    # 로그인 실패 확인 - 로그인 페이지 유지
    current_url = page.url
    assert "login" in current_url or "mybox" not in current_url
    assert page.locator('#new_btn_login, [name="company_code"], [name="id"]').count() > 0
