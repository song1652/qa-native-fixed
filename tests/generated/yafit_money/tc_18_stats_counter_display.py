from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_stats_counter_display(page):
    """누적 보상액 카운터 표시"""
    page.goto(BASE_URL)
    page.wait_for_load_state("domcontentloaded")

    expect(page.get_by_text("37억원을 벌어갔어요").first).to_be_visible()
    expect(page.get_by_text("벌써 11만명의 돈버는 운동 회원분들이").first).to_be_visible()
    # .count-up section contains the live numeric counter (e.g. "3,768,753,153")
    assert page.locator('.count-up').count() > 0
