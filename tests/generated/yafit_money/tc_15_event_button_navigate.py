
BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_event_button_navigate(page):
    """이벤트 버튼 클릭 시 이벤트 목록 페이지로 이동"""
    page.goto(BASE_URL)

    # .btn-m-event is mobile-only (display:none at desktop); use visible desktop .btn-event
    btn = page.locator('.btn-event')
    onclick = btn.get_attribute('onclick')
    assert onclick is not None, "'.btn-event' button has no onclick attribute"
    assert 'event/list' in onclick, f"Expected 'event/list' in onclick, got: {onclick}"
