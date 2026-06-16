import json
from pathlib import Path
from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_login_and_buy_annual_light(page):
    """로그인 후 연간 라이트 결제 주문 페이지 이동"""
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        test_data = json.load(f)["yafit_money"]

    page.goto(BASE_URL)

    page.evaluate(
        "document.querySelector('.price-box.yearly .buy-button').dispatchEvent("
        "new MouseEvent('click', {bubbles:true, cancelable:true}))"
    )
    page.locator(".login-iframe > iframe").wait_for(state="visible", timeout=8000)
    page.wait_for_timeout(1000)

    frame = page.frame_locator('.login-iframe > iframe')
    expect(frame.get_by_placeholder('아이디를 입력해주세요.')).to_be_visible(timeout=8000)
    frame.get_by_placeholder('아이디를 입력해주세요.').fill(test_data["valid_user"]["username"])
    frame.get_by_placeholder('비밀번호를 입력해주세요.').fill(test_data["valid_user"]["password"])
    frame.get_by_role('button', name='야나두 계정으로 로그인').click()

    # After login popup closes, redirect to promo page; re-click buy to reach cart
    page.wait_for_load_state("domcontentloaded", timeout=10000)
    page.wait_for_timeout(1500)

    if "mypage/order/cart/detail" not in page.url:
        page.evaluate(
            "document.querySelector('.price-box.yearly .buy-button').dispatchEvent("
            "new MouseEvent('click', {bubbles:true, cancelable:true}))"
        )
        page.wait_for_url("**/mypage/order/cart/detail/**", timeout=10000)

    assert "yanadoo.co.kr/mypage/order/cart/detail" in page.url

    order_text_visible = (
        page.locator("text=야핏사이클 라이트 플랜").count() > 0
        or page.locator("text=주문 상품").count() > 0
    )
    assert order_text_visible, "Expected '야핏사이클 라이트 플랜' or '주문 상품' text on the page"

    # Navigate back to base URL to drain pending cross-domain requests before context closes
    try:
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=5000)
    except Exception:
        pass
