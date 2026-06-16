
BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_page_load(page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    assert page.title() == "야핏사이클 | 돈버는 운동 야핏"
    content = page.content()
    assert "달린 거리만큼" in content
    assert "당신의 운동 습관이 돈이 됩니다!" in content
