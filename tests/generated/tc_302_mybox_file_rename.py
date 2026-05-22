"""DirectCloud: tc_302 - 마이박스 — 파일 이름 변경"""
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


def test_tc_302_mybox_file_rename(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    creds = data["directcloud"]["valid_user"]
    rename_filename = data["directcloud"]["rename_filename"]

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
        pytest.skip("마이박스에 파일이 없어 이름 변경 테스트 불가")

    # 우클릭 → 이름변경 메뉴
    files.first.click(button='right')
    page.wait_for_timeout(800)

    rename_menu = page.locator('.contextmenu-item:has-text("이름변경")')
    assert rename_menu.count() > 0, "컨텍스트 메뉴에서 이름변경 항목을 찾을 수 없습니다"
    rename_menu.first.click(timeout=5000)
    page.wait_for_timeout(800)

    # 이름 변경 다이얼로그 "새 이름을 입력하세요." 가 열려야 함
    rename_input = page.locator('.modal input[type="text"], dialog input[type="text"]')
    if rename_input.count() == 0:
        # fallback: 현재 파일명이 선택된 일반 input
        rename_input = page.locator('input[type="text"]:not([placeholder="검색"])')
    assert rename_input.count() > 0, "이름 변경 입력창이 표시되지 않습니다"
    rename_input.first.click(click_count=3)
    rename_input.first.fill(rename_filename)

    # "이름변경" 확인 버튼 클릭
    confirm_btn = page.locator('button:has-text("이름변경"):not(.contextmenu-item)')
    if confirm_btn.count() == 0:
        confirm_btn = page.locator('button:has-text("확인"), button[type="submit"]')
    assert confirm_btn.count() > 0, "이름변경 확인 버튼을 찾을 수 없습니다"
    confirm_btn.first.click(timeout=5000)
    page.wait_for_timeout(2000)
    dismiss_popups(page)

    # 변경된 파일명이 목록에 반드시 표시돼야 통과
    # rename_filename 예: "renamed_by_test.txt" → 확장자 제외한 부분으로 검색
    name_part = rename_filename.rsplit('.', 1)[0] if '.' in rename_filename else rename_filename
    renamed = page.locator(f'text={name_part}')
    assert renamed.count() > 0, f"변경된 파일명 '{rename_filename}'이 목록에 표시되지 않습니다"
    assert renamed.first.is_visible(), f"'{name_part}'이 보이지 않습니다"
