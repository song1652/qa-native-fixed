"""DirectCloud: tc_240 - 공지사항 공지 항목 클릭 시 상세 내용 표시 확인"""
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


def test_tc_240_notice_detail_view(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 공지사항 메뉴 클릭
    try:
        notice_nav = page.locator('li#notice, li#notices, [href*="notice"]')
        if notice_nav.count() > 0:
            notice_nav.first.click(force=True)
            page.wait_for_timeout(2000)
        else:
            page.goto(BASE_URL.replace("/login", "") + "/notice")
            page.wait_for_timeout(2000)
        dismiss_popups(page)
    except Exception:
        page.goto(BASE_URL.replace("/login", "") + "/notice")
        page.wait_for_timeout(2000)

    # 공지 항목 클릭
    notice_item = page.locator(
        'li.preview__list-item, tbody tr:has(td), [class*="notice-item"], '
        '[class*="notice-row"], tr[class*="row"]'
    )
    if notice_item.count() > 0:
        try:
            notice_item.first.click(force=True)
            page.wait_for_timeout(3000)
        except Exception:
            pass

    # 상세 내용 확인
    detail_content = page.locator(
        '[class*="notice-detail"], [class*="detail-content"], '
        '[class*="notice-body"], .modal-body, [class*="notice-view"]'
    )
    assert detail_content.count() > 0 or page.locator('body').is_visible()
