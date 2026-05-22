"""
자동 생성된 Playwright 테스트 코드
URL: https://web.directcloud.jp/login
케이스: tc_09_search_functionality (검색 기능)
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def login(page, company_code, user_id, password):
    """로그인"""
    page.goto(BASE_URL)
    page.wait_for_timeout(1000)
    page.fill('[name="company_code"]', company_code)
    page.fill('[name="id"]', user_id)
    page.fill('[name="password"]', password)
    page.click('#new_btn_login')
    try:
        page.wait_for_url("**/home**", timeout=20000)
    except Exception:
        page.goto(BASE_URL)
        page.wait_for_timeout(3000)
        page.fill('[name="company_code"]', company_code)
        page.fill('[name="id"]', user_id)
        page.fill('[name="password"]', password)
        page.click('#new_btn_login')
        page.wait_for_url("**/home**", timeout=20000)


def test_tc_09_search_functionality(page):
    """검색 기능"""
    with open(str(TEST_DATA_PATH), 'r', encoding='utf-8') as f:
        test_data = json.load(f)

    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])

    # 검색 입력 필드 확인
    page.wait_for_load_state('networkidle')

    search_input = page.locator('[placeholder="검색"]')
    assert search_input.is_visible(), "검색 입력 필드(검색창)가 표시되지 않습니다"
    # 검색어 입력 확인
    search_input.fill("test")
    assert "test" in search_input.input_value(), "검색어가 입력되지 않습니다"
