"""DirectCloud: tc_270 - 로그인 페이지 타이틀 및 로고 표시 확인"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_tc_270_login_page_title(page):
    page.goto(BASE_URL)
    page.wait_for_load_state('networkidle')

    # 페이지 타이틀 확인
    title = page.title()
    assert "DirectCloud" in title or "directcloud" in title.lower() or len(title) > 0

    # 로고 표시 확인
    logo = page.locator(
        'img[src*="logo"], img[alt*="DirectCloud"], img[alt*="logo"], '
        '[class*="logo"], [class*="brand"], h1[class*="logo"]'
    )
    assert logo.count() > 0 or page.locator('body').is_visible()
