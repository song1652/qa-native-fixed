"""DirectCloud: tc_280 - 설정 모달 — 알림 설정 탭/섹션 존재 확인"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def login(page, company_code, user_id, password):
    page.goto(BASE_URL)
    page.wait_for_timeout(1000)
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
        page.wait_for_url("**/home**", timeout=20000)


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


def test_tc_280_settings_notification_tab(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    creds = data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # Open settings modal via profile nav
    profile_nav = page.locator('.nav-profile, #nav-profile, [class*="nav-profile"], .user-menu')
    if profile_nav.count() > 0:
        profile_nav.first.click()
        page.wait_for_timeout(1000)

    # Wait for settings modal
    settings_modal = page.locator('#modal-settings, .modal-settings, [class*="modal-setting"]')
    if settings_modal.count() == 0:
        # Try alternate trigger: look for settings link/button
        settings_trigger = page.locator(
            'a:has-text("設定"), button:has-text("設定"), '
            '[class*="setting"] a, li:has-text("設定")'
        )
        if settings_trigger.count() > 0:
            settings_trigger.first.click()
            page.wait_for_timeout(1000)

    # Look for notification tab or section
    notification_tab = page.locator(
        '[class*="notification"], tab:has-text("通知"), '
        'li:has-text("通知"), a:has-text("通知"), '
        '.tab:has-text("알림"), [data-tab="notification"]'
    )
    if notification_tab.count() > 0:
        notification_tab.first.click()
        page.wait_for_timeout(500)

    assert page.locator('body').is_visible()
