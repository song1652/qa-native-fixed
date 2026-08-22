"""
tc_03_checkout_flow.py
- 로그인 → 상품 추가 → 장바구니 → 체크아웃 정보 입력 → 주문 완료 확인
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
"""
import json
import re
from pathlib import Path

from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"
TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def test_checkout_flow(page: Page):
    """장바구니 체크아웃 전체 플로우 완료 후 'Thank you for your order!' 확인"""
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    username = data["saucedemo"]["valid_user"]
    password = data["saucedemo"]["valid_password"]
    first_name = data["saucedemo"]["checkout"]["first_name"]
    last_name = data["saucedemo"]["checkout"]["last_name"]
    postal_code = data["saucedemo"]["checkout"]["postal_code"]

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

    # 장바구니 아이템 존재 확인 후 체크아웃 진행 (SauceDemo: .cart_item CSS class)
    page.locator('.cart_item').first.wait_for(state="visible", timeout=10000)
    page.locator('[data-test="checkout"]').click()
    page.wait_for_load_state("networkidle")

    # 체크아웃 정보 입력
    page.locator('[data-test="firstName"]').fill(first_name)
    page.locator('[data-test="lastName"]').fill(last_name)
    page.locator('[data-test="postalCode"]').fill(postal_code)
    page.locator('[data-test="continue"]').click()
    page.wait_for_load_state("networkidle")

    # 주문 요약 소계 표시 확인
    expect(page.locator('[data-test="subtotal-label"]')).to_be_visible()

    # 주문 완료
    page.locator('[data-test="finish"]').click()
    page.wait_for_load_state("networkidle")

    # 완료 헤더 및 메시지 확인
    complete_header = page.locator('[data-test="complete-header"]')
    complete_header.wait_for(state="visible", timeout=10000)
    expect(complete_header).to_contain_text("Thank you for your order!")

    page.screenshot(path="tests/screenshots/tc_03_checkout_flow.png")
