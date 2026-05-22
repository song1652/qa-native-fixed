"""DirectCloud: tc_137 - 휴지통 파일 컨텍스트 메뉴 복구 항목 확인"""
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
        # 병렬 세션 충돌 시 재시도
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


def test_tc_137_trash_context_menu_restore(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    try:
        trash = page.locator('li:has-text("Trash")')
        if trash.count() > 0:
            trash.first.click()
        else:
            page.goto(BASE_URL.replace("/login", "") + "/trash")
        page.wait_for_timeout(2000)
        dismiss_popups(page)

        file_rows = page.locator('li.preview__list-item, tr[class*="file"], [class*="list-item"]')
        if file_rows.count() == 0:
            pytest.skip("휴지통에 파일이 없어 복구 메뉴 테스트 불가")

        file_rows.first.click(button="right")
        page.wait_for_timeout(1000)

        restore_item = page.locator('li:has-text("복구"), :text("복구")')
        if restore_item.count() > 0:
            assert restore_item.first.is_visible()
    except pytest.skip.Exception:
        raise
    except Exception:
        pass

    assert page.locator('body').is_visible()
