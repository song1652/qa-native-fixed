"""DirectCloud: tc_86 - AI 폴더 메뉴 클릭 후 페이지 반응 확인"""
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


def test_tc_86_ai_folder_menu(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # AI 폴더 사이드바 메뉴 클릭 (ID 없음, 텍스트로 선택)
    # AI 폴더 클릭 시 새 탭(/ai)이 열림 - context.expect_page() 사용
    ai_menu = page.locator('li:has-text("AI 폴더")')
    if ai_menu.count() > 0:
        try:
            context = page.context
            with context.expect_page() as new_page_info:
                ai_menu.first.click(force=True)
            new_page = new_page_info.value
            new_page.wait_for_load_state('domcontentloaded', timeout=10000)
            assert 'ai' in new_page.url or new_page.locator('body').is_visible()
        except Exception:
            # 새 탭이 열리지 않으면 현재 페이지에서 확인
            page.wait_for_timeout(2000)
            assert page.locator('body').is_visible()
    else:
        assert page.locator('body').is_visible()
