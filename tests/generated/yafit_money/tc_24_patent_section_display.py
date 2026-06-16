"""
자동 생성된 Playwright 테스트 코드
URL: https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html
케이스: patent_section_display (tc_24)

Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_patent_section_display(page):
    """특허 섹션 기술 항목 표시"""
    page.goto(BASE_URL)
    page.wait_for_load_state("domcontentloaded")

    expect(page.get_by_text("특허 제 10-2032224호")).to_be_visible()
    expect(page.get_by_text("운동도 보상도")).to_be_visible()
    expect(page.get_by_text("돈 버는 재미는 똑같아요")).to_be_visible()
