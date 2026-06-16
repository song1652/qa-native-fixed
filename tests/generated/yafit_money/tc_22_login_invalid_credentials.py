import json
from pathlib import Path
from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_login_invalid_credentials(page):
    """잘못된 계정 정보 로그인 실패"""
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        test_data = json.load(f)["yafit_money"]

    page.goto(BASE_URL)
    page.wait_for_load_state("domcontentloaded")

    page.evaluate(
        "document.querySelector('.price-box.yearly .buy-button').dispatchEvent("
        "new MouseEvent('click', {bubbles:true, cancelable:true}))"
    )
    page.locator(".login-iframe > iframe").wait_for(state="visible", timeout=6000)

    frame = page.frame_locator(".login-iframe > iframe")
    expect(frame.get_by_placeholder("아이디를 입력해주세요.")).to_be_visible()
    frame.get_by_placeholder("아이디를 입력해주세요.").fill(test_data["invalid_user"]["username"])
    frame.get_by_placeholder("비밀번호를 입력해주세요.").fill(test_data["invalid_user"]["password"])
    frame.get_by_role("button", name="야나두 계정으로 로그인").click()
    page.wait_for_timeout(2000)

    assert "order/cart/detail" not in page.url
    expect(page.locator(".login-iframe")).to_be_visible()
