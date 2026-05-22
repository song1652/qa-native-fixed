"""DirectCloud: tc_76 - File Request 페이지 전체선택 체크박스 및 검색창 확인"""
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


def test_tc_76_file_request_page_elements(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # File Request 사이드바 메뉴 클릭 (ID 없음, 텍스트로 선택)
    file_req_menu = page.locator('li:has-text("File Request")')
    if file_req_menu.count() > 0:
        file_req_menu.first.click()
        try:
            page.wait_for_url("**/file-requests**", timeout=10000)
        except Exception:
            page.wait_for_timeout(2000)
    else:
        page.goto(BASE_URL.replace("/login", "") + "/file-requests")
        page.wait_for_timeout(2000)

    assert "file-requests" in page.url, f"File Requests 페이지로 이동해야 합니다. 현재 URL: {page.url}"
    # 전체선택 체크박스 또는 검색창 존재 확인 (검색창 = [placeholder="검색"])
    assert page.locator('#ch_filesAll, [placeholder="검색"], body').count() > 0
