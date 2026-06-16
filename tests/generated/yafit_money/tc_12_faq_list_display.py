from pathlib import Path

BASE_URL = "https://yafit.yanadoo.co.kr/yanadoo/promotion/yafitMoney.html"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_faq_list_display(page):
    """FAQ 목록 12개 항목 표시"""
    page.goto(BASE_URL)

    faq_count = page.locator('.faq-title').count()
    assert faq_count == 12, f"Expected 12 FAQ items, got {faq_count}"

    # FAQ titles include a "구매 필수" / "사용필수" / "기타" prefix span before the title text
    titles = page.locator('.faq-title').all_inner_texts()
    assert any('구매 전 꼭 확인해주세요' in t for t in titles), "FAQ '구매 전 꼭 확인해주세요' not found"
    assert any('마일리지 적립' in t for t in titles), "FAQ '마일리지 적립' not found"
    assert any('환불 규정' in t for t in titles), "FAQ '환불 규정' not found"
