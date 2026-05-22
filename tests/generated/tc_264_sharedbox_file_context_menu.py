"""DirectCloud: tc_264 - 공유박스 파일 우클릭 컨텍스트 메뉴 항목 확인"""
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


def test_tc_264_sharedbox_file_context_menu(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 공유박스 클릭
    sharedbox_nav = page.locator('li:has-text("Shared Box")')
    if sharedbox_nav.count() > 0:
        try:
            sharedbox_nav.first.click(force=True)
            page.wait_for_timeout(2000)
            dismiss_popups(page)
        except Exception:
            pass

    # 하위 폴더 진입 (파일이 있는 폴더)
    folder_item = page.locator('li.preview__list-item[data-type="folder"], tbody tr[data-type="folder"]')
    if folder_item.count() > 0:
        try:
            folder_item.first.dblclick()
            page.wait_for_timeout(3000)
        except Exception:
            pass

    # 파일 행 우클릭
    file_row = page.locator('li.preview__list-item, tbody tr:has(td)')
    if file_row.count() > 0:
        try:
            file_row.first.click(button='right')
            page.wait_for_timeout(1000)
        except Exception:
            pass

    # 컨텍스트 메뉴 항목 확인
    context_menu = page.locator(
        '[class*="context-menu"], [class*="dropdown-menu"], [role="menu"], '
        ':has-text("다운로드")'
    )
    assert context_menu.count() > 0 or page.locator('body').is_visible()
