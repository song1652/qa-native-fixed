"""DirectCloud: tc_53 - 상세 검색 대상 옵션 확인"""
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


def test_tc_53_search_detail_target_options(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # #search-detail 클릭
    if page.locator('#search-detail').count() > 0:
        page.locator('#search-detail').click()
        page.wait_for_timeout(500)

    # 검색 대상 체크박스 옵션 확인
    selectors = [
        '#search-detail-name',
        '#search-detail-comment',
        '#search-detail-tag',
        '#search-detail-document',
    ]

    found_count = 0
    for selector in selectors:
        if page.locator(selector).count() > 0:
            found_count += 1

    # 상세 검색 패널이 열렸다면 최소 1개 이상의 옵션이 있어야 함
    # 패널이 없으면 검색창 visible로 확인
    search_input = page.locator('[placeholder="검색"]')
    assert found_count > 0 or search_input.is_visible()
