"""
자동 생성된 Playwright 테스트 코드
URL: https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html
케이스: footer_links_display (tc_25)

Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_footer_links_display(page):
    """푸터 주요 링크 표시"""
    page.goto(BASE_URL)
    page.wait_for_load_state("domcontentloaded")

    expect(page.get_by_text("주식회사 야나두")).to_be_visible()
    expect(page.get_by_role("link", name="이용약관")).to_be_visible()
    expect(page.get_by_role("link", name="환불규정안내")).to_be_visible()
    expect(page.get_by_role("link", name="개인정보처리방침")).to_be_visible()

    assert page.get_by_role("link", name="아이폰 앱 다운로드").is_visible()
