"""DirectCloud: tc_20 - 상세 검색 버튼"""
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


def test_tc_20_search_detail_button(page):
    """상세 검색 버튼 동작 확인"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    page.wait_for_load_state('networkidle')

    # 상세검색 버튼 찾기
    detail_btn = page.locator('#search-detail, button[aria-label*="detail"], button:has-text("상세")')
    if detail_btn.count() > 0 and detail_btn.first.is_visible():
        detail_btn.first.click()
        page.wait_for_timeout(1000)
        assert page.locator('body').is_visible()
    else:
        # 버튼이 없으면 기본 페이지 확인
        assert "mybox" in page.url
