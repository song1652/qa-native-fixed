from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_login_popup_form(page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.evaluate(
        "document.querySelector('.price-box.yearly .buy-button').dispatchEvent("
        "new MouseEvent('click', {bubbles: true, cancelable: true}))"
    )
    page.locator(".login-iframe > iframe").wait_for(state="visible", timeout=8000)
    page.wait_for_timeout(1000)
    frame = page.frame_locator(".login-iframe > iframe")
    expect(frame.get_by_placeholder("아이디를 입력해주세요.")).to_be_visible(timeout=8000)
    expect(frame.get_by_text("로그인 상태 유지")).to_be_visible(timeout=8000)
    expect(frame.get_by_role("button", name="아이디 찾기")).to_be_visible(timeout=8000)
    expect(frame.get_by_role("button", name="회원가입하기")).to_be_visible(timeout=8000)
