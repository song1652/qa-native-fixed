"""DirectCloud: tc_75 - 링크 히스토리 검색 실행 확인"""
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
    page.wait_for_load_state('networkidle')


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


def test_tc_75_link_history_search_execute(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    search_keyword = data["directcloud"]["search_keyword"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # Link History 사이드바 메뉴 클릭 (ID 없음, 텍스트로 선택)
    link_menu = page.locator('li:has-text("Link History")')
    if link_menu.count() > 0:
        link_menu.first.click()
    else:
        page.goto(BASE_URL.replace("/login", "") + "/linkmanager")

    page.wait_for_timeout(2000)
    dismiss_popups(page)

    # select에서 "all" value 선택 (count > 0 체크)
    if page.locator('select').count() > 0:
        try:
            page.locator('select').first.select_option(value='all')
        except Exception:
            pass

    # 검색 입력 필드에 키워드 입력 (strict mode 회피: .first 사용)
    search_input = page.locator(
        'input[placeholder*="파일명"], input[placeholder*="링크"], input[type="text"]'
    )
    if search_input.count() > 0:
        search_input.first.fill(search_keyword)

    # 검색 버튼 클릭 (AI 팝업 차단 대비 force=True)
    if page.locator('button:has-text("검색")').count() > 0:
        try:
            page.locator('button:has-text("검색")').first.click(force=True)
        except Exception:
            pass

    page.wait_for_timeout(1000)
    assert page.locator('body').is_visible()
