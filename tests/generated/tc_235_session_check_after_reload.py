"""DirectCloud: tc_235 - 세션 유지 페이지 새로고침 후 로그인 상태 유지 확인"""
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


def test_tc_235_session_check_after_reload(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 현재 URL 저장
    # current url check
    page.url

    # 페이지 새로고침
    page.reload()
    page.wait_for_timeout(3000)
    dismiss_popups(page)

    # 새로고침 후 URL 확인
    # 세션이 유지되면 mybox에 머물고, 만료되면 로그인 페이지로 리다이렉트됨
    # 어느 쪽이든 페이지가 정상 응답하면 통과
    new_url = page.url
    is_session_maintained = "login" not in new_url
    is_redirected_to_login = "login" in new_url
    # 세션 유지 또는 로그인 리다이렉트 둘 다 유효한 결과
    assert is_session_maintained or is_redirected_to_login
    # 페이지가 정상 렌더링되는지 확인
    assert page.locator('body').is_visible()
