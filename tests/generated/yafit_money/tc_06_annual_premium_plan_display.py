from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_annual_premium_plan_display(page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    yearly = page.locator('.price-box.yearly')
    expect(yearly.locator('h3').filter(has_text='프리미엄').first).to_be_visible()
    expect(yearly.get_by_text("BEST").first).to_be_visible()
    expect(yearly.get_by_text("최대할인").first).to_be_visible()
    expect(yearly.get_by_text("33,250원").first).to_be_visible()
    expect(yearly.get_by_text("1년 399,000원").first).to_be_visible()
    expect(yearly.get_by_text("44% 할인").first).to_be_visible()
    expect(yearly.get_by_text("최대 55만 마일리지 적립").first).to_be_visible()
    expect(yearly.get_by_text("365 챌린지 성공 마일리지").first).to_be_visible()
