"""DirectCloud: tc_80 - Shared Box 파일 업로드 input 존재 확인"""
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


def test_tc_80_sharedbox_upload_input_exists(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # Shared Box 사이드바 메뉴 클릭 (ID 없음, 텍스트로 선택)
    sb_menu = page.locator('li:has-text("Shared Box")')
    if sb_menu.count() > 0:
        sb_menu.first.click()
        try:
            page.wait_for_url("**/sharedbox**", timeout=10000)
        except Exception:
            page.wait_for_timeout(2000)
    else:
        page.goto(BASE_URL.replace("/login", "") + "/sharedbox")
        page.wait_for_timeout(2000)

    page.wait_for_timeout(3000)
    assert "sharedbox" in page.url, f"Shared Box 페이지로 이동해야 합니다. 현재 URL: {page.url}"
    assert page.locator('#fileuploadBtn, input[type="file"]').count() > 0, \
        "파일 업로드 input이 존재해야 합니다."
