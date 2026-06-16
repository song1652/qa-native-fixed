"""
자동 생성된 Playwright 테스트 코드
URL: https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html
케이스: faq_accordion_open (tc_10)

Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from pathlib import Path
from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_faq_accordion_open(page):
    """FAQ 항목 클릭 시 내용 펼쳐짐"""
    page.goto(BASE_URL)

    page.locator('.faq-title').first.click()
    page.wait_for_timeout(500)

    expect(page.locator('.faq-contents').first).to_be_visible()
