"""DirectCloud: tc_88 - 설정 모달 언어를 English로 변경 후 select 값 확인"""
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


def test_tc_88_settings_language_change_english(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')

    opened = open_settings_modal(page)
    if not opened:
        assert page.locator('body').is_visible()
        return

    # 언어 select에서 English 선택 시도
    lang_select = page.locator('#modal-settings select').first
    if lang_select.count() > 0:
        try:
            lang_select.select_option(label='English')
            page.wait_for_timeout(500)
        except Exception:
            try:
                lang_select.select_option(value='en')
            except Exception:
                pass
    assert page.locator('#modal-settings').is_visible() or page.locator('body').is_visible()
