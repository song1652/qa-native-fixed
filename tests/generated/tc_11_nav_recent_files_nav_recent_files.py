"""
자동 생성된 Playwright 테스트 코드
URL: https://web.directcloud.jp/login
케이스: tc_11_nav_recent_files (tc_11_nav_recent_files)

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
    """로그인 헬퍼 - 각 파일이 독립적으로 소유"""
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


def test_tc_11_nav_recent_files(page):
    """최근파일 메뉴 이동 및 페이지 로드"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)

    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])

    page.locator('li:has-text("최근파일")').first.click()
    page.wait_for_url("**/recents**", timeout=10000)

    assert "/recents" in page.url
    # 검색창 또는 파일 목록이 있으면 통과 (페이지 로드 확인)
    page.wait_for_timeout(1000)
    assert (
        page.locator('[placeholder="검색"]').count() > 0
        or page.locator('li.preview__list-item').count() > 0
        or page.locator('ul.table-files').count() > 0
    ), "최근파일 페이지가 로드되지 않았습니다"
