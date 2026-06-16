from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_annual_tab_default_active(page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    active_text = page.evaluate("document.querySelector('button.active')?.innerText")
    assert active_text is not None, "활성 탭 버튼을 찾을 수 없음"
    assert "연간 결제" in active_text
    expect(page.get_by_text("8,250원").first).to_be_visible()
