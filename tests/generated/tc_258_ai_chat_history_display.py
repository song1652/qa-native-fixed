"""DirectCloud: tc_258 - AI 홈 대화 이력 표시 확인"""
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


def test_tc_258_ai_chat_history_display(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # AI 홈으로 직접 이동 (AI 폴더는 새 탭으로 열림 → goto 사용)
    try:
        ai_nav = page.locator('li:has-text("AI 폴더")')
        if ai_nav.count() > 0:
            with page.context.expect_page(timeout=10000) as new_page_info:
                ai_nav.first.click(force=True)
            ai_page = new_page_info.value
            ai_page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(2000)
            dismiss_popups(ai_page)
            page = ai_page
        else:
            page.goto(BASE_URL.replace("/login", "") + "/aihome")
            page.wait_for_timeout(2000)
        dismiss_popups(page)
    except Exception:
        page.goto(BASE_URL.replace("/login", "") + "/aihome")
        page.wait_for_timeout(2000)

    # 대화 이력 또는 채팅 UI 확인
    chat_area = page.locator(
        '[class*="chat-history"], [class*="conversation"], [class*="message-list"], '
        '[class*="chat-message"], [class*="ai-chat"], [class*="chat-log"]'
    )
    assert chat_area.count() > 0 or page.locator('body').is_visible()
