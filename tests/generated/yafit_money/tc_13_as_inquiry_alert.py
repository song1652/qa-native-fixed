from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_as_inquiry_alert(page):
    """A/S 안내 사항 FAQ 항목 클릭 후 전화번호 링크 확인"""
    page.goto(BASE_URL)

    # A/S FAQ accordion item
    as_faq = page.locator('.faq-title').filter(has_text='A/S 안내 사항')
    expect(as_faq).to_be_visible()
    as_faq.click()
    page.wait_for_timeout(500)

    # Tel link becomes visible inside expanded accordion content
    tel_link = page.get_by_role("link", name="1600-0563").first
    expect(tel_link).to_be_visible()
    href = tel_link.get_attribute("href")
    assert href is not None and "1600" in href, f"Phone number not in href: {href}"
