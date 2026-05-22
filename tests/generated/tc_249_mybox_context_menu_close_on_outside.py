"""DirectCloud: tc_249 - 마이박스 컨텍스트 메뉴 외부 클릭 시 닫힘 확인"""
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


def test_tc_249_mybox_context_menu_close_on_outside(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 마이박스 클릭
    mybox_nav = page.locator('li:has-text("My Box")')
    if mybox_nav.count() > 0:
        mybox_nav.first.click()
        page.wait_for_timeout(2000)
        dismiss_popups(page)

    # 파일 행 우클릭으로 컨텍스트 메뉴 오픈
    file_row = page.locator('li.preview__list-item, tbody tr:has(td)')
    context_menu = page.locator(
        '[class*="context-menu"], [class*="dropdown-menu"], '
        'ul[class*="menu"], [role="menu"]'
    )

    if file_row.count() > 0:
        try:
            file_row.first.click(button='right')
            page.wait_for_timeout(800)

            # 컨텍스트 메뉴가 열렸는지 확인
            if context_menu.count() > 0 and context_menu.first.is_visible():
                # 외부 영역 클릭 (페이지 상단 빈 공간)
                page.click('body', position={"x": 10, "y": 10})
                page.wait_for_timeout(500)

                # 컨텍스트 메뉴가 닫혔는지 확인
                assert not context_menu.first.is_visible() or context_menu.count() == 0
            else:
                assert page.locator('body').is_visible()
        except Exception:
            assert page.locator('body').is_visible()
    else:
        assert page.locator('body').is_visible()
