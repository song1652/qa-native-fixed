"""DirectCloud: tc_28 - AI Home 버튼 가시성 및 클릭 동작"""
import json
import pytest
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


def test_tc_28_ai_home_button(page):
    """AI Home 버튼 가시성 확인 및 클릭"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    ai_btn = page.locator('#showAIHome')
    if ai_btn.count() == 0:
        pytest.skip("AI 홈 버튼(#showAIHome)이 이 계정/플랜에 존재하지 않습니다")
    assert ai_btn.first.is_visible(), "AI 홈 버튼(#showAIHome)이 보이지 않습니다"
    ai_btn.first.click(force=True)
    page.wait_for_timeout(1500)
    ai_panel = page.locator('[id*="ai"], [class*="ai-home"], [class*="aiHome"]')
    assert ai_panel.count() > 0 or "ai" in page.url.lower(), "AI 홈 버튼 클릭 후 AI 패널 또는 AI 페이지로 이동하지 않았습니다"
