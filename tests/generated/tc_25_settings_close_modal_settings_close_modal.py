"""DirectCloud: tc_25 - 설정 모달 닫기"""
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
                if (style.position === 'fixed' || parseInt(style.zIndex) > 100) el.remove();
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
    try:
        page.locator('#modal-settings').wait_for(state='visible', timeout=20000)
        return True
    except Exception:
        return False


def test_tc_25_settings_close_modal(page):
    """설정 모달 닫기 (X 버튼) — 닫은 후 모달이 사라졌는지 확인"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    page.wait_for_load_state('networkidle')

    opened = open_settings_modal(page)
    assert opened, "설정 모달이 열리지 않았습니다"

    modal = page.locator('#modal-settings')
    assert modal.count() > 0 and modal.is_visible(), "설정 모달(#modal-settings)이 열리지 않았습니다"

    # 닫기 버튼 클릭
    close_btn = page.locator('#modal-settings button.close')
    assert close_btn.count() > 0, "설정 모달에 닫기 버튼(button.close)이 없습니다"
    close_btn.first.click()
    page.wait_for_timeout(1000)

    # 모달이 닫혔는지 확인
    assert modal.count() == 0 or not modal.is_visible(), "설정 모달이 닫히지 않았습니다"
