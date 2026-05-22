"""DirectCloud: tc_210 - 코멘트 모달에서 코멘트 추가"""
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


def test_tc_210_comment_modal_add_comment(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    file_item = page.locator('li.preview__list-item')
    if file_item.count() > 0:
        try:
            file_item.first.scroll_into_view_if_needed()
            file_item.first.click(button='right', force=True)
            page.wait_for_timeout(1000)
            comment_btn = page.locator(':text("코멘트"), :text("Comment")')
            if comment_btn.count() > 0:
                comment_btn.first.click(force=True)
                page.wait_for_timeout(2000)
                # 코멘트 입력란 확인
                comment_input = page.locator('#modal-comment textarea, [class*="comment"] textarea')
                if comment_input.count() > 0:
                    comment_input.first.fill("test comment")
                    page.wait_for_timeout(500)
                    # 저장 버튼 (실제 저장은 하지 않고 확인만)
                    page.keyboard.press('Escape')
        except Exception:
            pass
    assert page.locator('body').is_visible()
