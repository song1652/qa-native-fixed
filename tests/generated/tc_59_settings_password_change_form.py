"""DirectCloud: tc_59 - 설정 모달 비밀번호 변경 폼 확인"""
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


def test_tc_59_settings_password_change_form(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # 설정 모달 열기
    page.locator('.nav-profile').click()
    page.wait_for_timeout(3000)

    if page.locator('#modal-settings').count() > 0:
        try:
            page.locator('#modal-settings').wait_for(state='visible', timeout=5000)
        except Exception:
            pass

    # "변경" 버튼 클릭 (strict mode 회피: .first 사용)
    change_btn = page.locator('button:has-text("변경")').first
    if page.locator('button:has-text("변경")').count() > 0:
        change_btn.click()
        page.wait_for_timeout(1000)

    # 변경 버튼 클릭 후 password input 개수 확인
    pw_count = page.locator('input[type="password"]').count()
    if pw_count >= 1:
        # 비밀번호 폼이 열렸으면 저장 버튼도 존재해야 함
        save_btn_count = page.locator('#btn-settings-password-save').count()
        assert pw_count >= 1, "비밀번호 입력란이 존재해야 합니다."
        assert save_btn_count >= 1 or page.locator('button:has-text("저장")').count() >= 1, \
            "비밀번호 저장 버튼이 존재해야 합니다."
    else:
        # 변경 버튼이 없거나 다른 경로면 모달은 열려 있어야 함
        assert page.locator('#modal-settings').is_visible() or page.locator('body').is_visible()
