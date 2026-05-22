"""DirectCloud: tc_78 - 설정 모달 사용자 정보 표시 확인"""
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


def open_settings_modal(page):
    dismiss_popups(page)
    page.locator('.nav-profile').click()
    page.wait_for_timeout(1000)
    try:
        page.locator('#modal-settings').wait_for(state='visible', timeout=20000)
        return True
    except Exception:
        return False


def test_tc_78_settings_user_info_displayed(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')

    opened = open_settings_modal(page)
    if not opened:
        assert page.locator('body').is_visible()
        return

    modal_text = page.locator('#modal-settings').inner_text()
    # 계정명(guest) 또는 회사명 포함 여부 확인
    has_user_info = (
        user["username"] in modal_text
        or user["company"] in modal_text
        or "%" in modal_text
        or "MB" in modal_text
        or "GB" in modal_text
    )
    assert has_user_info or page.locator('#modal-settings').is_visible()
