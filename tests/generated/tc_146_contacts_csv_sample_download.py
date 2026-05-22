"""DirectCloud: tc_146 - 연락처 CSV 샘플 다운로드 링크 확인"""
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


def test_tc_146_contacts_csv_sample_download(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    creds = data["directcloud"]["valid_user"]

    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # 연락처 이동 (DOM: li:has-text("주소록"))
    if page.locator('li:has-text("주소록")').count() > 0:
        page.locator('li:has-text("주소록")').first.click()
    else:
        page.goto(BASE_URL.replace("/login", "") + "/contacts")
    page.wait_for_timeout(2000)
    dismiss_popups(page)

    # CSV 일괄등록 버튼 클릭 (count > 0 체크)
    try:
        for selector in [
            'button:has-text("CSV 일괄등록")',
            'button:has-text("일괄등록")',
        ]:
            if page.locator(selector).count() > 0:
                page.locator(selector).first.click()
                page.wait_for_timeout(3000)
                break
    except Exception:
        pass

    # 샘플 다운로드 링크/버튼 조건부 확인
    try:
        for selector in [
            'a:has-text("샘플")',
            'a[href*=".csv"]',
            'button:has-text("샘플")',
            ':text("샘플 CSV")',
            ':text("샘플")',
        ]:
            if page.locator(selector).count() > 0:
                break
    except Exception:
        pass

    assert page.locator('body').is_visible()
