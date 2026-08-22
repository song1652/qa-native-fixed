"""
tc_02_remove_from_cart.py
- 로그인 후 상품 추가 → 장바구니 이동 → 삭제 → 장바구니가 비어있는지 확인
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
"""
import json
import re
from pathlib import Path

from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"
TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def test_remove_from_cart(page: Page):
    """장바구니에서 상품 삭제 후 장바구니가 비어있는지 검증"""
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
    # 인벤토리 URL로 완전 전환 대기 (networkidle 단독 불충분)
    page.wait_for_url(re.compile(r"/inventory"), timeout=15000)
    page.wait_for_load_state("networkidle")

    # 인벤토리에서 상품 추가 (Sauce Labs Backpack)
    add_btn = page.locator('[data-test="add-to-cart-sauce-labs-backpack"]')
    add_btn.wait_for(state="visible", timeout=10000)
    add_btn.click()
    # 배지가 "1"로 업데이트 확인 (cart에 추가됐음을 보장)
    expect(page.locator('[data-test="shopping-cart-badge"]')).to_contain_text("1", timeout=10000)

    # 장바구니로 이동
    page.locator('[data-test="shopping-cart-link"]').click()
    page.wait_for_url(re.compile(r"/cart"), timeout=10000)
    page.wait_for_load_state("networkidle")

    # 삭제 전 아이템이 존재하는지 확인 (SauceDemo는 .cart_item CSS class 사용)
    cart_item = page.locator('.cart_item').first
    cart_item.wait_for(state="visible", timeout=10000)

    # 삭제 버튼 클릭 (data-test^="remove" 패턴 유효)
    remove_btn = page.locator('[data-test^="remove"]').first
    remove_btn.wait_for(state="visible", timeout=10000)
    remove_btn.click()
    page.wait_for_load_state("networkidle")

    # 삭제 후 장바구니가 비어있는지 확인 (.cart_item 요소가 없음)
    assert page.locator('.cart_item').count() == 0, (
        "삭제 후 장바구니에 아이템이 남아있음"
    )

    page.screenshot(path="tests/screenshots/tc_02_remove_from_cart.png")
