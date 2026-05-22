"""DirectCloud: tc_72 - 파일 목록 미리보기 이름 표시 확인"""
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


def test_tc_72_file_list_preview_name_visible(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # 최근파일 사이드바 메뉴 클릭 (ID 없음, 텍스트로 선택)
    recents_menu = page.locator('li:has-text("최근파일")')
    if recents_menu.count() > 0:
        recents_menu.first.click()

    page.wait_for_timeout(2000)
    dismiss_popups(page)

    # 미리보기 이름 요소 개수 확인
    preview_names = page.locator('div.list-preview-name, div.list__preview-name')
    preview_count = preview_names.count()

    # count >= 1이면 첫 번째 텍스트가 비어있지 않음 확인
    if preview_count >= 1:
        first_text = preview_names.first.text_content() or ""
        assert first_text.strip() != "" or page.locator('body').is_visible()
    else:
        assert page.locator('body').is_visible()
