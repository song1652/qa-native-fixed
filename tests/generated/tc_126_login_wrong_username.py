"""DirectCloud: tc_126 - 잘못된 사용자명으로 로그인 시도"""
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


def test_tc_126_login_wrong_username(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    valid_user = data["directcloud"]["valid_user"]
    invalid_user = data["directcloud"]["invalid_user"]

    page.goto(BASE_URL)
    page.fill('[name="company_code"]', valid_user["company"])
    page.fill('[name="id"]', invalid_user["username"])
    page.fill('[name="password"]', valid_user["password"])
    page.click('#new_btn_login')
    page.wait_for_timeout(3000)

    assert "login" in page.url or page.locator('[name="id"]').count() > 0
