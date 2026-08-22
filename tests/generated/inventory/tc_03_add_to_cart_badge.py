"""
tc_03_add_to_cart_badge.py
- 로그인 후 inventory.html에서 첫 번째 상품 "Add to cart" 클릭 시
  장바구니 배지가 "1"로 업데이트됨을 확인
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
"""
import json
import re
from pathlib import Path

from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"
TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def test_add_to_cart_badge(page: Page):
    """첫 번째 상품 Add to cart 클릭 후 장바구니 배지가 1로 변경됨을 확인"""
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

    # 장바구니 배지가 초기에 없음을 확인
    cart_badge = page.locator('[data-test="shopping-cart-badge"]')
    assert cart_badge.count() == 0, "Cart badge should not be visible before adding items"

    # 첫 번째 "Add to cart" 버튼 클릭
    add_to_cart_btn = page.locator('[data-test^="add-to-cart"]').first
    add_to_cart_btn.wait_for(state="visible", timeout=10000)
    add_to_cart_btn.click()

    # 장바구니 배지가 "1"로 표시됨
    expect(cart_badge).to_be_visible()
    expect(cart_badge).to_contain_text("1")

    page.screenshot(path="tests/screenshots/tc_03_add_to_cart_badge.png")
