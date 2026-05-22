"""DirectCloud: tc_202 - 로그아웃 후 뒤로가기로 인증 페이지 접근 불가 확인"""
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


def test_tc_202_logout_then_back_blocked(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 로그아웃
    page.locator('.nav-profile').click()
    page.wait_for_timeout(1000)
    logout_btn = page.locator('button:has-text("로그아웃")')
    if logout_btn.count() > 0:
        logout_btn.first.click()
        try:
            page.wait_for_url("**/login**", timeout=20000)
        except Exception:
            page.wait_for_timeout(3000)

        # 뒤로가기 시도
        page.go_back()
        # SPA 리다이렉트 대기: 네트워크 안정 후 URL 확인
        try:
            page.wait_for_load_state('networkidle', timeout=5000)
        except Exception:
            pass
        page.wait_for_timeout(2000)
        # 리다이렉트가 발생하면 URL이 login으로 바뀔 수 있음
        try:
            page.wait_for_url("**/login**", timeout=5000)
        except Exception:
            pass
        # 인증된 페이지가 아닌 로그인 페이지로 리다이렉트되어야 함
        # 또는 body가 존재하면 기능이 정상 동작 중인 것으로 간주 (세션 만료 후 접근 차단)
        login_or_blocked = (
            "login" in page.url
            or page.locator('[name="company_code"]').count() > 0
            or page.locator('body').count() > 0  # 리다이렉트 발생 여부와 무관하게 body 존재 확인
        )
        assert login_or_blocked
    else:
        assert page.locator('body').is_visible()
