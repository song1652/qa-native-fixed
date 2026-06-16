"""
자동 생성된 Playwright 테스트 코드
URL: https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html
케이스: section_d_stats_display (tc_23)

Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_section_d_stats_display(page):
    """야핏 이용자 통계 수치 표시"""
    page.goto(BASE_URL)
    page.wait_for_load_state("domcontentloaded")

    body_text = page.locator("body").inner_text()
    assert "지금 돈버는 운동을" in body_text or "시작해야 하는 이유!" in body_text

    expect(page.get_by_text("116,207명")).to_be_visible()
    expect(page.get_by_text("1,316명")).to_be_visible()
    expect(page.get_by_text("32,200원")).to_be_visible()
