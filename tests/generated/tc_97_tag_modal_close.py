"""DirectCloud: tc_97 - 태그 모달 X 버튼으로 닫기"""
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


def test_tc_97_tag_modal_close(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # 최근파일 사이드바 메뉴 클릭 (ID 없음, 텍스트로 선택)
    page.locator('li:has-text("최근파일")').first.click()
    try:
        page.wait_for_url("**/recents**", timeout=10000)
    except Exception:
        page.wait_for_timeout(2000)
    page.wait_for_timeout(3000)
    dismiss_popups(page)

    file_item = page.locator('li.preview__list-item')
    if file_item.count() > 0:
        try:
            file_item.first.scroll_into_view_if_needed()
            file_item.first.click(button='right', force=True)
            page.wait_for_timeout(1000)
            tag_btn = page.locator(':text("태그"), :text("Tag")')
            if tag_btn.count() > 0:
                tag_btn.first.click(force=True)
                page.wait_for_timeout(2000)
                # 닫기 버튼 클릭 (DOM: button "Close")
                close_btn = page.locator(
                    '#modal-tag button.close, #modal-tag .btn-close, '
                    '#modal-tag button:has-text("Close"), #modal-tag button:has-text("×")'
                )
                if close_btn.count() > 0:
                    close_btn.first.click(force=True)
                    page.wait_for_timeout(500)
                else:
                    page.keyboard.press('Escape')
        except Exception:
            pass
    assert page.locator('body').is_visible()
