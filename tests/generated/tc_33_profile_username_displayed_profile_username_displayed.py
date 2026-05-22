"""DirectCloud: tc_33 - 사이드바 프로필 영역 사용자명 표시 확인"""
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


def test_tc_33_profile_username_displayed(page):
    """사이드바 프로필 영역 사용자명 표시 확인"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 프로필 영역 가시성 — DOM에서 heading[level=3] "게스트(guest)" 구조 확인
    profile = page.locator('.nav-profile')
    assert profile.count() > 0, "프로필 영역(.nav-profile)이 존재하지 않습니다"
    assert profile.first.is_visible(), "프로필 영역(.nav-profile)이 표시되지 않습니다"

    # 사용자명 h3 확인 (DOM: heading level=3 "게스트(guest)" 형태)
    username_el = page.locator('.nav-profile h3, h3[class*="profile"], h3[class*="user"]')
    if username_el.count() == 0:
        # h3가 직접 .nav-profile 내부에 없으면 텍스트 포함 여부 확인
        profile_text = profile.first.inner_text()
        assert len(profile_text.strip()) > 0, "프로필 영역에 사용자명이 표시되지 않습니다"
    else:
        text = username_el.first.inner_text()
        assert len(text.strip()) > 0, "사용자명(h3)이 비어 있습니다"
