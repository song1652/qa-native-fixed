"""DirectCloud: tc_23 - 설정 언어 선택"""
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
    """AI 팝업/오버레이 닫기"""
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    try:
        page.evaluate("""() => {
            const overlays = document.querySelectorAll('div[class*="sc-T"]');
            overlays.forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.position === 'fixed' || style.zIndex > 100) el.remove();
            });
        }""")
    except Exception:
        pass
    page.wait_for_timeout(200)


def open_settings_modal(page):
    """설정 모달 열기"""
    dismiss_popups(page)
    page.locator('.nav-profile').click()
    page.wait_for_timeout(1000)
    # #modal-settings가 표시될 때까지 대기 (최대 10초)
    try:
        page.locator('#modal-settings').wait_for(state='visible', timeout=20000)
        return True
    except Exception:
        return False


def test_tc_23_settings_language_select(page):
    """설정 모달 언어 선택 옵션 확인"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    page.wait_for_load_state('networkidle')

    opened = open_settings_modal(page)
    assert opened, "설정 모달이 열리지 않았습니다"

    # 설정 모달 내 언어 select: DOM에서 ID 없음, 모달 내 combobox 중 언어 옵션 포함한 것 찾기
    selects = page.locator('#modal-settings select').all()
    assert len(selects) > 0, "설정 모달에 select 요소가 없습니다"

    # 언어 옵션(한국어/English/日本語)을 포함한 select 찾기
    lang_found = False
    for sel in selects:
        if sel.is_visible():
            opts = sel.locator('option').all_text_contents()
            opt_text = ' '.join(opts)
            if any(lang in opt_text for lang in ['한국어', 'English', '日本語']):
                lang_found = True
                break
    assert lang_found, "설정 모달에 언어 옵션(한국어/English/日本語)이 포함된 select가 없습니다"
