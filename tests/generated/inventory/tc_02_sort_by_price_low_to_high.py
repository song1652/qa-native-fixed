"""
tc_02_sort_by_price_low_to_high.py
- 로그인 후 inventory.html에서 정렬 드롭다운을 "Price (low to high)"로 변경,
  첫 번째 상품 가격 ≤ 마지막 상품 가격임을 확인
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
"""
import json
import re
from pathlib import Path

from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"
TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def test_sort_by_price_low_to_high(page: Page):
    """정렬 드롭다운에서 Price (low to high) 선택 시 가격 오름차순 정렬됨을 확인"""
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    username = data["saucedemo"]["valid_user"]
    password = data["saucedemo"]["valid_password"]

    # 로그인
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    page.locator('[data-test="username"]').fill(username)
    page.locator('[data-test="password"]').fill(password)
    page.locator('[data-test="login-button"]').click()

    # 로그인 성공 확인
    expect(page).to_have_url(re.compile(r"/inventory"))
    page.wait_for_load_state("networkidle")

    # 정렬 드롭다운에서 "Price (low to high)" 선택
    sort_dropdown = page.locator('[data-test="product-sort-container"]')
    expect(sort_dropdown).to_be_visible()
    sort_dropdown.select_option("lohi")
    page.wait_for_load_state("networkidle")

    # 가격 목록 추출
    price_locators = page.locator('[data-test="inventory-item-price"]')
    price_count = price_locators.count()
    assert price_count >= 2, f"Expected at least 2 items for sort comparison, got {price_count}"

    prices = []
    for i in range(price_count):
        price_text = price_locators.nth(i).inner_text()
        # "$9.99" → 9.99
        price_value = float(price_text.replace("$", "").strip())
        prices.append(price_value)

    # 첫 번째 상품 가격 ≤ 마지막 상품 가격 (오름차순 확인)
    assert prices[0] <= prices[-1], (
        f"Price sort failed: first={prices[0]}, last={prices[-1]}. "
        f"Full list: {prices}"
    )

    page.screenshot(path="tests/screenshots/tc_02_sort_by_price_low_to_high.png")
