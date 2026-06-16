from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_monthly_tab_switch(page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.locator("button").filter(has_text="월간 결제").first.click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_text("9,900원").first).to_be_visible()
    expect(page.get_by_text("34,900원").first).to_be_visible()
    expect(page.get_by_text("39,900원").first).to_be_visible()
