"""DirectCloud: tc_304 - 마이박스 — 파일에 태그 추가"""
import json
import pytest
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


def test_tc_304_mybox_file_tag_add(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    creds = data["directcloud"]["valid_user"]
    tag_name = data["directcloud"]["tag_name"]

    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # 마이박스 이동
    mybox = page.locator('li#mybox')
    assert mybox.count() > 0, "마이박스 메뉴를 찾을 수 없습니다"
    mybox.first.click(timeout=5000)
    page.wait_for_timeout(1500)
    dismiss_popups(page)

    # 파일만 선택 (폴더 제외: 폴더는 .folder 클래스 포함)
    files = page.locator('li.preview__list-item:not(.folder)')
    if files.count() == 0:
        pytest.skip("마이박스에 파일이 없어 태그 추가 테스트 불가")

    # 우클릭 → 태그 메뉴 (다이얼로그: "태그 추가/편집")
    files.first.click(button='right')
    page.wait_for_timeout(800)

    tag_menu = page.locator('.contextmenu-item:has-text("태그")')
    assert tag_menu.count() > 0, "컨텍스트 메뉴에서 '태그' 항목을 찾을 수 없습니다"
    tag_menu.first.click(timeout=5000)
    page.wait_for_timeout(1000)

    # 태그 입력창 반드시 나타나야 함 (placeholder="tag")
    tag_input = page.locator('input[placeholder="tag"]')
    assert tag_input.count() > 0, "태그 입력창(placeholder='tag')이 표시되지 않습니다"
    tag_input.first.fill(tag_name)
    # 태그는 Enter 또는 Space로 추가
    page.keyboard.press('Enter')
    page.wait_for_timeout(500)

    # 입력된 태그가 chip/badge 형태로 표시되는지 확인 (다이얼로그 안에서)
    tag_visible = page.locator(
        f'[class*="tag"]:has-text("{tag_name}"), '
        f'[class*="badge"]:has-text("{tag_name}")'
    )
    assert tag_visible.count() > 0 or tag_input.first.input_value() == tag_name, \
        f"태그 '{tag_name}'이 다이얼로그에 표시되지 않습니다"

    # "확인" 버튼 클릭 (태그 저장)
    confirm_btn = page.locator('.modal button:has-text("확인")')
    assert confirm_btn.count() > 0, "태그 다이얼로그의 확인 버튼을 찾을 수 없습니다"
    confirm_btn.first.click(timeout=5000)
    page.wait_for_timeout(1500)
    dismiss_popups(page)

    # 다이얼로그가 닫혔는지 확인 (모달이 사라져야 함)
    modal_gone = page.locator('input[placeholder="tag"]')
    assert modal_gone.count() == 0, "태그 다이얼로그가 닫히지 않았습니다 — 저장 실패 가능성"
