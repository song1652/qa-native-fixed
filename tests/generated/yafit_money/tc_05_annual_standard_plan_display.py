from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_annual_standard_plan_display(page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(500)
    yearly = page.locator('.price-box.yearly')
    expect(yearly.locator('h3').filter(has_text='스탠다드').first).to_be_visible()
    expect(yearly.get_by_text("29,083원").first).to_be_visible()
    expect(yearly.get_by_text("1년 349,000원").first).to_be_visible()
    expect(yearly.get_by_text("27% 할인").first).to_be_visible()
    expect(yearly.get_by_text("최대 29만 마일리지 적립").first).to_be_visible()
    expect(yearly.get_by_text("365 챌린지 참여 불가").first).to_be_visible()
