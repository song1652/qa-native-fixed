from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_annual_light_plan_display(page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    # Monthly cards appear first in DOM (hidden); scope to .price-box.yearly to avoid picking up hidden duplicates
    yearly = page.locator('.price-box.yearly')
    expect(yearly.locator('h3').filter(has_text='라이트').first).to_be_visible()
    expect(yearly.get_by_text("8,250원").first).to_be_visible()
    expect(yearly.get_by_text("1년 99,000원").first).to_be_visible()
    expect(yearly.get_by_text("17% 할인").first).to_be_visible()
    expect(yearly.get_by_text("야핏 일부 콘텐츠 무제한 이용").first).to_be_visible()
    expect(yearly.get_by_text("마일리지 적립 불가").first).to_be_visible()
