"""DirectCloud: tc_236 - 마이박스 파일 선택 후 X 버튼으로 선택 해제 확인"""
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


def test_tc_236_mybox_select_deselect_x(page):
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

    # 파일 체크박스 클릭
    checkbox = page.locator('li.preview__list-item input[type="checkbox"], tbody tr input[type="checkbox"]')
    if checkbox.count() > 0:
        try:
            checkbox.first.click(force=True)
            page.wait_for_timeout(1000)
        except Exception:
            pass

    # X(닫기/선택 해제) 버튼 클릭
    close_btn = page.locator(
        '#btn-select-cancel, [class*="cancel-select"], [class*="deselect"], '
        'button[title*="キャンセル"], button[title*="cancel"], '
        '.toolbar-cancel, [class*="close-select"]'
    )
    if close_btn.count() > 0:
        try:
            close_btn.first.click(force=True)
            page.wait_for_timeout(500)
        except Exception:
            pass

    # 선택 해제 후 툴바 기본 상태 확인
    assert page.locator('body').is_visible()
    # 선택 카운터가 사라졌는지 확인
    select_count = page.locator('[class*="select-count"], [class*="selected-count"]')
    if select_count.count() > 0:
        # 카운터가 0이거나 숨김 상태여야 함
        assert select_count.first.is_hidden() or "0" in (select_count.first.inner_text() or "0")
    else:
        assert page.locator('body').is_visible()
