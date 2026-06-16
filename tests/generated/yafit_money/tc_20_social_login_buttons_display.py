from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_social_login_buttons_display(page):
    """로그인 팝업 소셜 로그인 버튼 표시"""
    page.goto(BASE_URL)
    page.wait_for_load_state("domcontentloaded")

    page.evaluate(
        "document.querySelector('.price-box.yearly .buy-button').dispatchEvent("
        "new MouseEvent('click', {bubbles:true, cancelable:true}))"
    )
    page.locator(".login-iframe > iframe").wait_for(state="visible", timeout=6000)

    frame = page.frame_locator(".login-iframe > iframe")
    expect(frame.get_by_role("button", name="카카오 로그인")).to_be_visible()
    expect(frame.get_by_role("button", name="애플 로그인")).to_be_visible()
    expect(frame.get_by_role("button", name="회원가입하기")).to_be_visible()
