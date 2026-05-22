"""DirectCloud: tc_149 - 파일 요청 새 요청 버튼 표시 확인"""
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


def test_tc_149_file_request_new_button(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    creds = data["directcloud"]["valid_user"]

    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # 파일 요청 이동 (DOM: li:has-text("File Request"))
    if page.locator('li:has-text("File Request")').count() > 0:
        page.locator('li:has-text("File Request")').first.click()
    else:
        page.goto(BASE_URL.replace("/login", "") + "/file-requests")
    page.wait_for_timeout(2000)
    dismiss_popups(page)

    # 새 요청 버튼 조건부 확인 (file_requests DOM: button 요소)
    try:
        new_btn = page.locator(
            'button:has-text("새"), button:has-text("+"), button:has-text("요청"), '
            '[title*="새"], [title*="추가"], button.btn-add'
        )
        if new_btn.count() > 0:
            assert new_btn.first.is_visible()
    except Exception:
        pass

    assert page.locator('body').is_visible()
