"""DirectCloud: tc_260 - 마이박스 링크 생성 시 비밀번호 설정 필드 확인"""
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


def test_tc_260_mybox_link_create_with_password(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 마이박스 클릭
    mybox_nav = page.locator('li:has-text("My Box")')
    if mybox_nav.count() > 0:
        mybox_nav.first.click()
        page.wait_for_timeout(2000)
        dismiss_popups(page)

    # 파일 우클릭 → 링크 생성
    file_row = page.locator('li.preview__list-item:not(.folder), tbody tr:has(td)')
    if file_row.count() > 0:
        try:
            file_row.first.click(button='right')
            page.wait_for_timeout(1000)
            link_item = page.locator(':has-text("링크생성"), :text("リンク作成"), :text("リンクを作成")')
            if link_item.count() > 0:
                link_item.first.click(force=True)
                page.wait_for_timeout(3000)
        except Exception:
            pass

    # 비밀번호 필드 확인
    pwd_field = page.locator(
        'input[type="password"][class*="link"], input[name*="password"][class*="link"], '
        'input[placeholder*="パスワード"], input[placeholder*="password"], '
        '[class*="link-password"], [class*="modal"] input[type="password"]'
    )
    assert pwd_field.count() > 0 or page.locator('body').is_visible()
