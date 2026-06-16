"""
자동 생성된 Playwright 테스트 코드
URL: https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html
케이스: nav_buy_button_navigate (tc_14)

Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from pathlib import Path

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_nav_buy_button_navigate(page):
    """네비게이션 구매하기 버튼 이동"""
    page.goto(BASE_URL)

    page.locator('.btn-nav-counsel').click()
    page.wait_for_load_state('domcontentloaded')

    assert 'yafitmembership' in page.url, f"Expected 'yafitmembership' in URL, got: {page.url}"
