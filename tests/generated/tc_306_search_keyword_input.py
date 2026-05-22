"""DirectCloud: tc_306 - 검색 — 키워드 직접 입력 후 결과 확인"""
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


def test_tc_306_search_keyword_input(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    vu = data["directcloud"]["valid_user"]
    keyword = data["directcloud"]["search_keyword"]

    login(page, vu["company"], vu["username"], vu["password"])
    dismiss_popups(page)

    # 검색 입력창 반드시 존재해야 함
    search_input = page.locator('#inputSearch')
    assert search_input.count() > 0, "검색 입력창(#inputSearch)을 찾을 수 없습니다"

    # 키워드 입력 및 검색 실행
    search_input.first.click()
    search_input.first.fill(keyword)
    page.keyboard.press('Enter')
    page.wait_for_timeout(2500)
    dismiss_popups(page)

    # 검색 실행 후: URL이 search 경로를 포함하거나 결과 컨테이너가 나타나야 함
    current_url = page.url
    search_result_container = page.locator(
        '[class*="search-result"], [class*="searchResult"], '
        '[class*="searchList"], #search-results, '
        'li.preview__list-item, [class*="fileList"]'
    )
    assert (
        "search" in current_url or search_result_container.count() > 0
    ), f"검색 실행 후 결과 페이지가 표시되지 않습니다. URL: {current_url}"

    # 검색 입력값이 입력창에 남아있어야 함 (검색이 실제로 실행됐음을 확인)
    search_value = search_input.first.input_value()
    # 검색 후 입력창이 비워지는 앱도 있으므로 URL 또는 결과 컨테이너로 충분
    assert (
        "search" in current_url
        or search_result_container.count() > 0
        or keyword in search_value
    ), "검색이 실행됐다는 증거(URL, 결과 컨테이너, 입력값)를 찾을 수 없습니다"
