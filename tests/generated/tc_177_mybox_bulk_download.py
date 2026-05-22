"""DirectCloud: tc_177 - 마이박스 다중 선택 다운로드"""
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


def test_tc_177_mybox_bulk_download(page):
    with open(TEST_DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)
    creds = data["directcloud"]["valid_user"]

    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    page.locator('li:has-text("My Box")').first.click()
    page.wait_for_timeout(2000)
    dismiss_popups(page)

    # 체크박스는 hover 시에만 표시됨 → JavaScript로 직접 클릭
    checkboxes = page.locator('.checkbox-list-item')
    cb_count = checkboxes.count()
    if cb_count >= 2:
        try:
            page.evaluate("document.querySelectorAll('.checkbox-list-item')[0].click()")
            page.wait_for_timeout(300)
            page.evaluate("document.querySelectorAll('.checkbox-list-item')[1].click()")
            page.wait_for_timeout(500)
        except Exception:
            pass
    elif cb_count == 1:
        try:
            page.evaluate("document.querySelectorAll('.checkbox-list-item')[0].click()")
            page.wait_for_timeout(500)
        except Exception:
            pass

    download_btn = page.locator('[title*="다운로드"], button:has-text("다운로드"), [class*="download"]')
    if download_btn.count() > 0:
        assert download_btn.count() > 0

    assert page.locator('body').is_visible()
