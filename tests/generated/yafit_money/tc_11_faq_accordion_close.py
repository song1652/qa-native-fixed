"""
자동 생성된 Playwright 테스트 코드
URL: https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html
케이스: faq_accordion_close (tc_11)

Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from pathlib import Path
from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_faq_accordion_close(page):
    """열린 FAQ 항목 재클릭 시 닫힘"""
    page.goto(BASE_URL)

    faq_title = page.locator('.faq-title').first

    faq_title.click()
    page.wait_for_timeout(300)

    faq_title.click()
    page.wait_for_timeout(300)

    expect(page.locator('.faq-contents').first).not_to_be_visible()
