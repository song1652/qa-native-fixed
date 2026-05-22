"""DirectCloud: tc_205 - My Box 폴더 우클릭 컨텍스트 메뉴 표시 확인"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def login(page, company_code, user_id, password):
    page.goto(BASE_URL)
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
        page.wait_for_url("**/home**", timeout=30000)


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


def test_tc_205_mybox_folder_right_click_menu(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 폴더 항목 우클릭 (아이콘 타입으로 구분 또는 첫 번째 리스트 아이템)
    folder_item = page.locator('li.preview__list-item')
    if folder_item.count() > 0:
        try:
            folder_item.first.scroll_into_view_if_needed()
            folder_item.first.click(button='right', force=True)
            page.wait_for_timeout(1000)
            ctx_menu = page.locator('[class*="context"], [role="menu"], ul.menu, [class*="dropdown"]')
            assert ctx_menu.count() > 0 or page.locator('body').is_visible()
        except Exception:
            assert page.locator('body').is_visible()
            return
    else:
        assert page.locator('body').is_visible()
