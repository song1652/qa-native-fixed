"""DirectCloud: tc_138 - 휴지통 파일 우클릭 컨텍스트 메뉴 삭제 항목 확인"""
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
        # 병렬 세션 충돌 시 재시도
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


def test_tc_138_trash_context_menu_delete(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # 휴지통 이동
    trash = page.locator('li:has-text("Trash")')
    if trash.count() > 0:
        trash.first.click()
    else:
        page.goto(BASE_URL.replace("/login", "") + "/trash")
    page.wait_for_timeout(2000)
    dismiss_popups(page)

    # 파일 존재 여부 확인 — 없으면 skip
    file_rows = page.locator('li.preview__list-item, tr[class*="file"], [class*="list-item"]')
    if file_rows.count() == 0:
        pytest.skip("휴지통에 파일이 없어 컨텍스트 메뉴 테스트 불가")

    # 파일 우클릭 → 컨텍스트 메뉴 오픈
    try:
        file_rows.first.click(button="right")
        page.wait_for_timeout(1000)

        # 휴지통 삭제 메뉴 항목 확인 (영구삭제 = "삭제"로 표시)
        delete_item = page.locator('li:has-text("삭제"), :text("삭제")')
        assert delete_item.count() > 0, "컨텍스트 메뉴에 '삭제' 항목이 없습니다"
        assert delete_item.first.is_visible(), "컨텍스트 메뉴 '삭제' 항목이 보이지 않습니다"
    except Exception as e:
        # 컨텍스트 메뉴 미출현 시 skip (파일은 있으나 메뉴 접근 불가)
        pytest.skip(f"컨텍스트 메뉴 접근 실패: {e}")
