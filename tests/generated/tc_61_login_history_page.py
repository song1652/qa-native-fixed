"""DirectCloud: tc_61 - 로그인 히스토리 페이지 이동 확인"""
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


def test_tc_61_login_history_page(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # 설정 모달 열기
    page.locator('.nav-profile').click()
    page.wait_for_timeout(3000)

    if page.locator('#modal-settings').count() > 0:
        try:
            page.locator('#modal-settings').wait_for(state='visible', timeout=5000)
        except Exception:
            pass

    # 상세 버튼 클릭 (count > 0 체크, strict mode 회피)
    if page.locator('button:has-text("상세")').count() > 0:
        page.locator('button:has-text("상세")').first.click()

    # 로그인 히스토리 URL로 이동 확인
    try:
        page.wait_for_url("**/login-history**", timeout=10000)
    except Exception:
        pass

    # 로그인 히스토리 페이지로 이동 확인
    assert "login-history" in page.url, f"로그인 히스토리 페이지로 이동해야 합니다. 현재 URL: {page.url}"
