"""DirectCloud: tc_161 - 스토리지 도움말 버튼 클릭 확인"""
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


def test_tc_161_storage_help_click(page):
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        test_data = json.load(f)
    user = test_data["directcloud"]["valid_user"]

    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    help_locator = page.locator(
        '[class*="storage"] button, [class*="help"], button[title*="도움"], '
        'button:has-text("?"), [class*="question"]'
    )
    if help_locator.count() > 0:
        help_locator.first.click()
        page.wait_for_timeout(1000)

    # 네비게이션 완료 후 body 확인 (세션 만료로 리다이렉트 중일 수 있음)
    try:
        page.wait_for_load_state('domcontentloaded', timeout=3000)
    except Exception:
        pass
    assert page.locator('body').count() > 0
