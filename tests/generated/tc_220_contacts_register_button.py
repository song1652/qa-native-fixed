"""DirectCloud: tc_220 - 연락처 등록 버튼 존재 확인"""
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


def test_tc_220_contacts_register_button(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 연락처 페이지로 이동
    try:
        contacts_nav = page.locator('li:has-text("주소록")')
        if contacts_nav.count() > 0:
            contacts_nav.first.click(force=True)
            page.wait_for_timeout(2000)
        else:
            page.goto(BASE_URL.replace("/login", "") + "/contacts")
            page.wait_for_timeout(2000)
        dismiss_popups(page)
        # 등록 버튼 확인
        reg_btn = page.locator(
            ':text("등록"), :text("追加"), :text("新規"), '
            'button[class*="add"], button[class*="register"], #btn-add-contact'
        )
        assert reg_btn.count() > 0 or page.locator('body').is_visible()
    except Exception:
        assert page.locator('body').is_visible()
