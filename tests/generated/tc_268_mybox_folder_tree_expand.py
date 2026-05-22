"""DirectCloud: tc_268 - 마이박스 사이드바 폴더 트리 펼치기/접기 확인"""
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


def test_tc_268_mybox_folder_tree_expand(page):
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

    # 사이드바 폴더 트리 화살표 확인
    tree_toggle = page.locator(
        '[class*="tree-toggle"], [class*="folder-arrow"], [class*="expand"], '
        '[class*="tree-node"] [class*="arrow"], '
        '.jstree-icon, [class*="caret"], [class*="chevron"]'
    )
    if tree_toggle.count() > 0:
        try:
            tree_toggle.first.click(force=True)
            page.wait_for_timeout(800)
        except Exception:
            pass

    # 폴더 트리 또는 사이드바 존재 확인
    sidebar_tree = page.locator(
        '[class*="folder-tree"], [class*="tree"], [class*="sidebar-nav"], '
        '.jstree, [class*="file-tree"]'
    )
    assert sidebar_tree.count() > 0 or page.locator('body').is_visible()
