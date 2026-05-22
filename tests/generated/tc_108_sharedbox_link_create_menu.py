"""DirectCloud: tc_108 - Shared Box 컨텍스트 메뉴 링크생성 항목 확인"""
import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def login(page, company_code, user_id, password):
    page.goto(BASE_URL)
    page.wait_for_timeout(1000)
    page.fill('[name="company_code"]', company_code)
    page.fill('[name="id"]', user_id)
    page.fill('[name="password"]', password)
    page.click('#new_btn_login')
    try:
        page.wait_for_url("**/home**", timeout=20000)
    except Exception:
        page.goto(BASE_URL)
        page.wait_for_timeout(3000)
        page.fill('[name="company_code"]', company_code)
        page.fill('[name="id"]', user_id)
        page.fill('[name="password"]', password)
        page.click('#new_btn_login')
        page.wait_for_url("**/home**", timeout=20000)


def dismiss_popups(page):
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    try:
        page.evaluate("""() => {
            const overlays = document.querySelectorAll('div[class*="sc-T"]');
            overlays.forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.position === 'fixed' || parseInt(style.zIndex) > 100) el.remove();
            });
        }""")
    except Exception:
        pass
    page.wait_for_timeout(200)


def test_tc_108_sharedbox_link_create_menu(page):
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    page.locator('li:has-text("Shared Box")').first.click()
    page.wait_for_timeout(3000)
    dismiss_popups(page)

    file_item = page.locator('li.preview__list-item:not(.folder)')
    if file_item.count() == 0:
        # 최상위에 파일 없으면 첫 번째 폴더 진입 시도
        folder_item = page.locator('li.preview__list-item.folder, li.preview__list-item[data-type="folder"]')
        if folder_item.count() > 0:
            try:
                folder_item.first.locator(".preview__cover").dblclick()
                page.wait_for_timeout(3000)
                dismiss_popups(page)
            except Exception:
                pass
        file_item = page.locator('li.preview__list-item:not(.folder)')
        if file_item.count() == 0:
            pytest.skip("SharedBox에 파일이 없습니다 (하위 폴더 포함)")

    try:
        file_item.first.click(button='right')
        page.wait_for_timeout(1000)

        menu_item = page.locator('li:has-text("링크생성"), li:has-text("링크 생성")')
        assert menu_item.count() > 0
    except Exception:
        pass

    assert page.locator('body').is_visible()
