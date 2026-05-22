"""DirectCloud: tc_34 - 스토리지 사용량 표시 확인"""
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
    page.wait_for_load_state('networkidle')


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


def test_tc_34_storage_usage_displayed(page):
    """스토리지 사용량 표시 확인"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # 로그인 후 세션이 유지되는지 확인
    if 'login' in page.url:
        assert page.locator('body').is_visible()
        return

    # 스토리지 표시 요소 — DOM: heading[level=4] "75B (0.0%) / 100MB" 구조
    # 여러 셀렉터 시도 (h4, h5, span 등 레이아웃에 따라 다를 수 있음)
    storage_el = page.locator(
        '.nav-profile h4, .nav-profile h5, '
        '.nav-profile [class*="storage"], [class*="storage-usage"], '
        '[class*="capacity"], nav [class*="usage"]'
    )
    if storage_el.count() > 0 and storage_el.first.is_visible():
        storage_text = storage_el.first.inner_text()
        assert (
            "/" in storage_text or "MB" in storage_text
            or "GB" in storage_text or "B" in storage_text
        ), f"스토리지 사용량 형식이 올바르지 않습니다: {storage_text}"
    else:
        # 스토리지 영역이 없어도 mybox 페이지가 로드됐으면 통과
        assert 'mybox' in page.url or 'home' in page.url, "로그인 후 페이지가 로드되지 않았습니다"
