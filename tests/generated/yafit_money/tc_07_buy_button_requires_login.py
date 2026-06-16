from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_buy_button_requires_login(page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.evaluate(
        "document.querySelector('.price-box.yearly .buy-button').dispatchEvent("
        "new MouseEvent('click', {bubbles: true, cancelable: true}))"
    )
    page.locator(".login-iframe > iframe").wait_for(state="visible", timeout=8000)
    # Allow extra time for iframe content to fully load before asserting
    page.wait_for_timeout(1000)
    frame = page.frame_locator(".login-iframe > iframe")
    expect(frame.get_by_placeholder("아이디를 입력해주세요.")).to_be_visible(timeout=8000)
    expect(frame.get_by_role("button", name="야나두 계정으로 로그인")).to_be_visible(timeout=8000)
