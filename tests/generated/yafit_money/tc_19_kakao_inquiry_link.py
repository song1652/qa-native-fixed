"""
자동 생성된 Playwright 테스트 코드
URL: https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html
케이스: kakao_inquiry_link (tc_19)

Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from playwright.sync_api import expect

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"


def test_kakao_inquiry_link(page):
    """카카오 문의 링크 href 확인"""
    page.goto(BASE_URL)
    page.wait_for_load_state("domcontentloaded")

    link = page.get_by_role("link", name="야핏 이용권 & 앱 문의하기")
    expect(link).to_be_visible()

    href = link.get_attribute("href")
    assert href == "http://pf.kakao.com/_xmCkrG"
