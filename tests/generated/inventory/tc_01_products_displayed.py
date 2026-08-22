"""
tc_01_products_displayed.py
- 로그인 후 inventory.html에서 상품 목록이 표시되는지 확인
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
"""
import json
import re
from pathlib import Path

from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"
TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def test_products_displayed(page: Page):
    """로그인 후 인벤토리 페이지에서 상품 목록이 정상 표시됨을 확인"""
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

    # 상품 목록 컨테이너가 표시됨
    inventory_container = page.locator('[data-test="inventory-container"]')
    expect(inventory_container).to_be_visible()

    # 상품 아이템이 1개 이상 존재
    items = page.locator('[data-test="inventory-item"]')
    item_count = items.count()
    assert item_count >= 1, f"Expected at least 1 inventory item, got {item_count}"

    # 첫 번째 상품의 이름과 가격이 표시됨
    first_item = items.first
    expect(first_item.locator('[data-test="inventory-item-name"]')).to_be_visible()
    expect(first_item.locator('[data-test="inventory-item-price"]')).to_be_visible()

    page.screenshot(path="tests/screenshots/tc_01_products_displayed.png")
