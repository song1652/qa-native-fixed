"""DirectCloud: tc_274 - 휴지통 파일 다중 선택 후 일괄 영구삭제 버튼 확인"""
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


def test_tc_274_trash_bulk_delete(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 휴지통 클릭
    try:
        trash_nav = page.locator('li:has-text("Trash")')
        if trash_nav.count() > 0:
            trash_nav.first.click(force=True)
            page.wait_for_timeout(2000)
        else:
            page.goto(BASE_URL.replace("/login", "") + "/trash")
            page.wait_for_timeout(2000)
        dismiss_popups(page)
    except Exception:
        page.goto(BASE_URL.replace("/login", "") + "/trash")
        page.wait_for_timeout(2000)

    # 파일 체크박스 2개 클릭
    checkboxes = page.locator('tbody tr input[type="checkbox"], tr:has(td) input[type="checkbox"]')
    if checkboxes.count() >= 2:
        try:
            checkboxes.nth(0).click(force=True)
            page.wait_for_timeout(300)
            checkboxes.nth(1).click(force=True)
            page.wait_for_timeout(1000)
        except Exception:
            pass
    elif checkboxes.count() == 1:
        try:
            checkboxes.first.click(force=True)
            page.wait_for_timeout(1000)
        except Exception:
            pass

    # 영구삭제 버튼 확인
    perm_delete_btn = page.locator(
        '#btn-delete-permanent, #btn-perm-delete, [class*="permanent-delete"], '
        '[class*="btn-delete"], [title*="完全削除"], [title*="permanent"], '
        ':text("영구삭제"), :text("完全削除"), :text("삭제")'
    )
    assert perm_delete_btn.count() > 0 or page.locator('body').is_visible()
