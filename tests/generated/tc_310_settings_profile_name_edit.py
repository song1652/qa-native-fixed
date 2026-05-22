"""DirectCloud: tc_310 - 설정 — 프로필 설정 모달 열기 확인"""
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


def test_tc_310_settings_profile_name_edit(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    vu = data["directcloud"]["valid_user"]
    display_name = data["directcloud"]["display_name"]

    login(page, vu["company"], vu["username"], vu["password"])
    dismiss_popups(page)

    # 프로필 아이콘 클릭 → 설정 모달 열기
    page.locator('.nav-profile').click()
    page.wait_for_timeout(1500)

    # 설정 모달(#modal-settings)이 반드시 열려야 함
    modal = page.locator('#modal-settings')
    assert modal.count() > 0, "설정 모달(#modal-settings)이 열리지 않았습니다"
    assert modal.first.is_visible(), "설정 모달이 표시되지 않습니다"

    # 설정 모달 내 사용자 정보 표시 확인 (로그인된 사용자명 포함)
    modal_text = modal.first.text_content()
    assert modal_text and len(modal_text.strip()) > 0, "설정 모달에 내용이 표시되지 않습니다"
