import re
from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_monthly_light_plan_price(page):
    """월간 라이트 플랜 가격 표시"""
    page.goto(BASE_URL)
    page.wait_for_load_state("domcontentloaded")

    page.locator("button").filter(has_text=re.compile(r"^월간 결제$")).first.click()
    page.wait_for_timeout(1000)

    # After tab switch, .card.monthly cards become visible
    light_card = page.locator('.card.monthly').first
    expect(light_card.get_by_text("9,900원")).to_be_visible()
    expect(light_card.get_by_text("118,800원")).to_be_visible()

    standard_card = page.locator('.card.monthly').nth(1)
    expect(standard_card.get_by_text("34,900원")).to_be_visible()
