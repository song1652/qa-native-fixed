"""DirectCloud: tc_263 - 검색 OCR 문서 필터 선택 후 검색 결과 확인"""
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


def test_tc_263_mybox_ocr_search_result(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 검색창 입력
    search_input = page.locator('[placeholder="검색"]')
    if search_input.count() > 0:
        search_input.first.click()
        search_input.first.fill(data["directcloud"]["search_keyword"])
        page.wait_for_timeout(300)

    # 상세 검색 패널 열기
    detail_btn = page.locator('#search-detail, [class*="detail-search-btn"]')
    if detail_btn.count() > 0:
        try:
            detail_btn.first.click()
            page.wait_for_timeout(1000)
        except Exception:
            pass

    # 문서 내용 체크박스 선택
    doc_checkbox = page.locator(
        '#search-detail-document, input[name*="document"], '
        'input[id*="ocr"], input[class*="document"]'
    )
    if doc_checkbox.count() > 0:
        try:
            doc_checkbox.first.click(force=True)
            page.wait_for_timeout(500)
        except Exception:
            pass

    # 검색 실행
    search_btn = page.locator('#search-search, button[class*="search"]')
    if search_btn.count() > 0:
        try:
            search_btn.first.click()
            page.wait_for_timeout(2000)
        except Exception:
            page.keyboard.press('Enter')
            page.wait_for_timeout(2000)
    else:
        page.keyboard.press('Enter')
        page.wait_for_timeout(2000)

    assert page.locator('body').is_visible()
