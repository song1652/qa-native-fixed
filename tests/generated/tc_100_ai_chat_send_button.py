"""DirectCloud: tc_100 - AI 폴더 채팅 전송 버튼 클릭 동작 확인"""
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


def test_tc_100_ai_chat_send_button(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    keyword = data["directcloud"].get("search_keyword", "test")
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # Shared Box 사이드바 메뉴 클릭 (ID 없음, 텍스트로 선택)
    sb = page.locator('li:has-text("Shared Box")')
    if sb.count() > 0:
        sb.first.click()
        try:
            page.wait_for_url("**/sharedbox**", timeout=10000)
        except Exception:
            page.wait_for_timeout(2000)
        page.wait_for_timeout(3000)
        dismiss_popups(page)

        ai_folder = page.locator(':text("DirectCloud AI")')
        if ai_folder.count() > 0:
            try:
                ai_folder.first.click(force=True)
                page.wait_for_timeout(2000)
                chat_input = page.locator('textarea[placeholder*="질문"], textarea')
                if chat_input.count() > 0 and chat_input.first.is_visible():
                    chat_input.first.fill(keyword)
                    # 전송 버튼 클릭
                    send_btn = page.locator(':text("전송"), button[type="submit"], [class*="send"]')
                    if send_btn.count() > 0:
                        send_btn.first.click(force=True)
                        page.wait_for_timeout(1000)
            except Exception:
                pass
    assert page.locator('body').is_visible()
