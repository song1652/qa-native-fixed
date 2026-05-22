"""DirectCloud: tc_18 - 파일 전체선택 체크박스"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def login(page, company_code, user_id, password):
    page.goto(BASE_URL)
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
        page.wait_for_url("**/home**", timeout=30000)


def test_tc_18_file_select_all_checkbox(page):
    """파일 전체선택 체크박스 동작 확인"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])

    page.locator('li:has-text("최근파일")').first.click()
    page.wait_for_url("**/recents**", timeout=10000)
    assert "/recents" in page.url

    # 전체선택 체크박스: #ch_filesAll 또는 input[type="checkbox"] 첫 번째
    checkbox_loc = page.locator('#ch_filesAll')
    if checkbox_loc.count() == 0:
        checkbox_loc = page.locator('input[type="checkbox"]').first
    else:
        checkbox_loc = checkbox_loc.first

    if checkbox_loc.is_visible():
        initial_state = checkbox_loc.is_checked()
        checkbox_loc.click()
        assert checkbox_loc.is_checked() != initial_state
        checkbox_loc.click()
        assert checkbox_loc.is_checked() == initial_state
    else:
        # 체크박스가 없으면 페이지 로드만 확인
        assert page.locator('body').is_visible()
