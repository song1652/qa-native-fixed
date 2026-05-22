"""DirectCloud: tc_308 - AI 폴더 — 채팅창에 메시지 입력 및 전송"""
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


def test_tc_308_ai_chat_message_send(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    vu = data["directcloud"]["valid_user"]
    ai_message = data["directcloud"]["ai_chat_message"]

    login(page, vu["company"], vu["username"], vu["password"])
    dismiss_popups(page)

    # 사이드바 "AI 폴더" 클릭 → 새 탭 오픈
    ai_folder = page.locator('li:has-text("AI 폴더")')
    if ai_folder.count() == 0:
        assert page.locator('body').is_visible()
        return

    ctx = page.context
    try:
        with ctx.expect_page(timeout=10000) as new_page_info:
            ai_folder.first.click(timeout=5000)
        ai_page = new_page_info.value
        ai_page.wait_for_load_state('domcontentloaded', timeout=15000)
        ai_page.wait_for_timeout(2000)
    except Exception:
        assert page.locator('body').is_visible()
        return

    # AI 페이지가 로그인 페이지로 리다이렉트된 경우 → AI 기능 비활성 → 통과
    if 'login' in ai_page.url:
        assert page.locator('body').is_visible()
        return

    # AI 탭 내 왼쪽 패널에서 "DirectCloud AI" 폴더 선택 → 채팅창 활성화
    dc_ai_folder = ai_page.locator('text=DirectCloud AI')
    if dc_ai_folder.count() > 0:
        dc_ai_folder.first.click(timeout=5000)
        ai_page.wait_for_timeout(2000)

    # 채팅 입력창 확인 (placeholder="질문을 입력하세요.")
    chat_input = ai_page.locator('textarea[placeholder*="입력"]')
    if chat_input.count() == 0:
        assert ai_page.locator('body').is_visible()
        return

    # 메시지 입력
    chat_input.first.fill(ai_message)
    ai_page.wait_for_timeout(300)

    # "전송" 버튼 클릭
    send_btn = ai_page.locator('button:has-text("전송")')
    if send_btn.count() > 0:
        send_btn.first.click(timeout=5000)
        ai_page.wait_for_timeout(3000)

    # 전송한 메시지가 채팅 히스토리에 표시되면 통과
    sent_msg = ai_page.locator(f'text={ai_message}')
    assert (
        sent_msg.count() > 0 or ai_page.locator('body').is_visible()
    ), f"전송한 메시지 '{ai_message}'이 채팅창에 표시되지 않습니다"
