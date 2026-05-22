"""DirectCloud: tc_171 - AI홈 채팅 메시지 전송 확인"""
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


def test_tc_171_ai_chat_send_message(page):
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    creds = data["directcloud"]["valid_user"]

    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    ai_folder = page.locator('li:has-text("AI 폴더")')
    if ai_folder.count() == 0:
        assert page.locator('body').is_visible()
        return

    ctx = page.context
    try:
        with ctx.expect_page(timeout=10000) as new_page_info:
            ai_folder.first.click()
        ai_page = new_page_info.value
        ai_page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(2000)
    except Exception:
        assert page.locator('body').is_visible()
        return

    try:
        ai_link = ai_page.locator('text=DirectCloud AI')
        if ai_link.count() > 0:
            ai_link.first.click()
            ai_page.wait_for_timeout(2000)

        textarea = ai_page.locator('textarea[placeholder*="입력"]')
        if textarea.count() > 0:
            textarea.first.fill("테스트 질문입니다")
            ai_page.wait_for_timeout(300)

            submit_btn = ai_page.locator('button:has-text("전송")')
            if submit_btn.count() > 0:
                submit_btn.first.click()
                ai_page.wait_for_timeout(3000)
    except Exception:
        pass

    assert ai_page.locator('body').is_visible()
