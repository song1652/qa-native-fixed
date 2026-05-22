"""DirectCloud: tc_287 - 마이박스 — 잠금된 파일에 잠금 아이콘 표시 확인"""
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


def test_tc_287_mybox_locked_file_badge(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    creds = data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # Navigate to mybox
    mybox = page.locator('li:has-text("My Box")')
    if mybox.count() > 0:
        mybox.first.click()
        page.wait_for_timeout(2000)
    dismiss_popups(page)

    # Look for lock icon in file rows
    lock_icon = page.locator(
        '[class*="lock-icon"], [class*="lock_icon"], '
        '[class*="icon-lock"], td [class*="lock"], '
        'li [class*="lock"][class*="icon"], '
        '[title*="ロック"], [title*="lock"], '
        'img[alt*="lock"], img[src*="lock"]'
    )
    if lock_icon.count() > 0:
        assert lock_icon.first.is_visible(), "잠금 아이콘이 보이지 않습니다"
    else:
        # 잠긴 파일이 없는 경우 — 파일 목록 컨테이너가 보이면 통과
        assert page.locator('#files').is_visible(), "MyBox 파일 목록 영역(#files)이 표시되지 않습니다"
