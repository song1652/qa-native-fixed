from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_allinone_link(page):
    """첫구매 혜택 받기 링크 href 확인"""
    page.goto(BASE_URL)
    page.wait_for_load_state("domcontentloaded")

    link = page.get_by_role("link", name="첫구매 혜택 받기")
    expect(link).to_be_visible()
    href = link.get_attribute("href")
    assert href is not None and "yafitAllInOne.html" in href, f"Expected 'yafitAllInOne.html' in href, got: {href}"
