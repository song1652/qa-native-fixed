"""
tc_01_cart_item_display.py
- 로그인 후 상품 추가 → 장바구니에 아이템 이름·가격·수량이 표시되는지 확인
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
"""
import json
import re
from pathlib import Path

from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"
TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def test_cart_item_display(page: Page):
    """장바구니에 추가한 상품이 이름·가격·수량과 함께 표시되는지 검증"""
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
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(re.compile(r"/inventory"))

    # 인벤토리에서 상품 추가 (Sauce Labs Backpack)
    page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click()

    # 장바구니로 이동
    page.locator('[data-test="shopping-cart-link"]').click()
    page.wait_for_load_state("networkidle")

    # 장바구니 아이템 존재 확인 (SauceDemo는 data-test="cart-item" 없음, CSS class 사용)
    cart_item = page.locator('.cart_item').first
    cart_item.wait_for(state="visible", timeout=10000)

    # 아이템 이름 표시 확인
    expect(page.locator('[data-test="inventory-item-name"]').first).to_be_visible()

    # 아이템 가격 표시 확인
    expect(page.locator('[data-test="inventory-item-price"]').first).to_be_visible()

    # 수량 표시 확인
    quantity = page.locator('[data-test="item-quantity"]').first
    expect(quantity).to_be_visible()
    expect(quantity).to_contain_text("1")

    page.screenshot(path="tests/screenshots/tc_01_cart_item_display.png")
