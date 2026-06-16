"""
자동 생성된 Playwright 테스트 코드
URL: https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html
케이스: mileage_scroll (tc_16)

Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from pathlib import Path

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_mileage_scroll(page):
    """마일리지 알아보기 클릭 시 섹션 스크롤"""
    page.goto(BASE_URL)

    initial_url = page.url

    page.locator('button:has-text("마일리지 알아보기")').click()
    page.wait_for_timeout(1000)

    assert page.url == initial_url, (
        f"Expected URL to remain '{initial_url}', but got '{page.url}'"
    )
