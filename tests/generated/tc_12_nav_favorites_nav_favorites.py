"""
자동 생성된 Playwright 테스트 코드
URL: https://web.directcloud.jp/login
케이스: tc_12_nav_favorites (tc_12_nav_favorites)

Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def login(page, company_code, user_id, password):
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
    page.wait_for_load_state('networkidle')


def test_tc_12_nav_favorites(page):
    """즐겨찾기 메뉴 이동 및 페이지 로드"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)

    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])

    page.locator('li:has-text("즐겨찾기")').first.click()
    page.wait_for_url("**/favorites**", timeout=10000)

    assert "/favorites" in page.url
    assert page.locator('[placeholder="검색"]').is_visible(), "즐겨찾기 페이지에 검색창이 표시되지 않습니다"
