"""데모용 의도적 실패 TC — 리포트 아티팩트(screenshot/video/trace/timing) 확인용."""
import pytest
from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


@pytest.mark.skip(reason="의도적 실패 데모 - 리포트 아티팩트 확인용, 정규 회귀 대상 아님")
def test_demo_intentional_fail(page):
    """존재하지 않는 버튼을 찾아서 의도적으로 실패시키는 데모 TC."""
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(1500)

    # 헤딩 확인 (통과)
    expect(page.locator("h1, h2, h3").first).to_be_visible(timeout=5000)

    # 의도적 실패: 존재하지 않는 요소
    expect(
        page.locator("#this-element-does-not-exist-for-demo")
    ).to_be_visible(timeout=3000)
