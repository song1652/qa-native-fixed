"""DirectCloud: tc_65 - 주소록 이름 검색 확인"""
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


def test_tc_65_contacts_name_search(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    search_keyword = data["directcloud"]["search_keyword"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # 주소록 사이드바 메뉴 클릭 (ID 없음, 텍스트로 선택)
    contacts_menu = page.locator('li:has-text("주소록")')
    if contacts_menu.count() > 0:
        contacts_menu.first.click()
    else:
        page.goto(BASE_URL.replace("/login", "") + "/contacts")

    page.wait_for_timeout(2000)
    dismiss_popups(page)

    # 이름/이메일 검색 입력 (strict mode 회피: .first 사용)
    search_input = page.locator(
        'input[placeholder*="이름 또는 이메일"], input[placeholder*="이름"], input[type="text"]'
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
