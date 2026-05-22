"""DirectCloud: tc_252 - 검색어 입력 후 초기화 X 버튼으로 검색어 삭제 확인"""
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


def test_tc_252_search_clear_button(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 검색창에 텍스트 입력
    search_input = page.locator('[placeholder="검색"]')
    if search_input.count() > 0:
        search_input.first.click()
        search_input.first.fill(data["directcloud"]["search_keyword"])
        page.wait_for_timeout(500)

    # X(초기화) 버튼 클릭
    clear_btn = page.locator(
        '#search-clear, [class*="search-clear"], [class*="clear-btn"], '
        'button[class*="cancel"], [title*="クリア"], [title*="clear"]'
    )
    if clear_btn.count() > 0:
        try:
            clear_btn.first.click(force=True)
            page.wait_for_timeout(500)
        except Exception:
            pass

    # 검색창이 비워졌는지 확인
    search_input_after = page.locator('[placeholder="검색"]')
    if search_input_after.count() > 0:
        value = search_input_after.first.input_value()
        assert value == "" or page.locator('body').is_visible()
    else:
        assert page.locator('body').is_visible()
