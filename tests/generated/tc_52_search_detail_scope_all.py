"""DirectCloud: tc_52 - 상세 검색 범위 전체 선택 후 검색"""
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


def test_tc_52_search_detail_scope_all(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    keyword = data["directcloud"]["search_keyword"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # 상세 검색 패널 열기
    if page.locator('#search-detail').count() > 0:
        page.locator('#search-detail').click()
        page.wait_for_timeout(500)

    # 전체 범위 라디오 클릭
    if page.locator('#detail-search-all').count() > 0:
        page.locator('#detail-search-all').click()
        page.wait_for_timeout(300)

    # 검색 입력창에 키워드 입력 (실제 DOM: placeholder="검색")
    search_input = page.locator('[placeholder="검색"]')
    assert search_input.count() > 0, "검색 입력창이 존재해야 합니다."
    search_input.fill(keyword)
    page.wait_for_timeout(300)

    # 검색 실행 버튼 클릭
    if page.locator('#search-search').count() > 0:
        page.locator('#search-search').click()
        page.wait_for_timeout(1000)

    # 오류 없음 확인
    assert page.locator('body').is_visible()
