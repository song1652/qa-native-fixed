"""DirectCloud: tc_08 - 파일/폴더 목록 영역 확인"""
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


def test_tc_08_file_list_area(page):
    """로그인 후 파일/폴더 목록 영역 확인"""
    with open(TEST_DATA_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    creds = test_data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])

    # home 또는 mybox에 착지 확인
    assert "mybox" in page.url or "home" in page.url

    # 페이지 완전 로드 및 팝업 처리
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(1500)
    try:
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
    except Exception:
        pass

    # 사이드바 mybox 메뉴 대기 후 클릭
    page.locator('li#mybox').wait_for(state='visible', timeout=10000)
    page.locator('li#mybox').click()
    page.wait_for_url("**/mybox**", timeout=10000)
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)

    # 파일 목록 영역 확인 (SPA 렌더링 대기)
    page.wait_for_selector('#files', state='visible', timeout=15000)
    assert page.locator('#files').is_visible(), "파일 목록 영역(#files)이 표시되지 않습니다"
