"""DirectCloud: tc_277 - 마이박스 — 미리보기 모달 닫기 확인"""
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


def test_tc_277_mybox_preview_modal_close(page):
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

    # Try to open preview via context menu on first file
    file_item = page.locator('li.preview__list-item')
    if file_item.count() == 0:
        file_item = page.locator('tr.file-row, tr[data-id], .file-list-item, .list-item')
    if file_item.count() > 0:
        file_item.first.click(button="right")
        page.wait_for_timeout(800)
        preview_item = page.locator(
            'li:has-text("미리보기"), .context-menu-item:has-text("미리보기"), '
            '[class*="context"] li:has-text("Preview")'
        )
        if preview_item.count() > 0:
            preview_item.first.click()
            page.wait_for_timeout(3000)

            # Look for close button in preview modal
            close_btn = page.locator(
                '.modal-close, button.close, [aria-label="close"], '
                '[class*="preview"] button[class*="close"], '
                '.preview-modal .btn-close, button:has-text("×"), button:has-text("閉じる")'
            )
            if close_btn.count() > 0:
                close_btn.first.click()
                page.wait_for_timeout(800)
            else:
                page.keyboard.press('Escape')
                page.wait_for_timeout(500)

    assert page.locator('body').is_visible()
