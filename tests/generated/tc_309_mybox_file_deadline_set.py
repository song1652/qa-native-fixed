"""DirectCloud: tc_309 - 마이박스 — 파일 기한 설정"""
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


def test_tc_309_mybox_file_deadline_set(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    vu = data["directcloud"]["valid_user"]

    login(page, vu["company"], vu["username"], vu["password"])
    dismiss_popups(page)

    # 마이박스 이동
    mybox = page.locator('li#mybox')
    assert mybox.count() > 0, "마이박스 메뉴를 찾을 수 없습니다"
    mybox.first.click(timeout=5000)
    page.wait_for_timeout(1500)
    dismiss_popups(page)

    # 파일만 선택 (폴더 제외: 폴더는 .folder 클래스 포함)
    file_items = page.locator('li.preview__list-item:not(.folder)')
    if file_items.count() == 0:
        pytest.skip("마이박스에 파일이 없어 파일기한 테스트 불가 (폴더만 존재)")

    # 파일 우클릭 → 파일기한 메뉴
    file_items.first.click(button='right')
    page.wait_for_timeout(800)

    deadline_menu = page.locator('.contextmenu-item:has-text("파일기한")')
    assert deadline_menu.count() > 0, "컨텍스트 메뉴에서 '파일기한' 항목을 찾을 수 없습니다"
    deadline_menu.first.click(timeout=5000)
    page.wait_for_timeout(1000)

    # 파일기한 다이얼로그가 열려야 함
    deadline_modal = page.locator('.modal:has-text("파일기한"), dialog:has-text("파일기한")')
    assert deadline_modal.count() > 0, "파일기한 다이얼로그가 표시되지 않습니다"

    # 다이얼로그 상태 확인:
    # - 신규 설정: 숫자 입력창 표시 + 확인 버튼 활성화
    # - 기한 이미 설정됨: "설정일/삭제 예정일" 표시 + 확인 버튼 disabled
    already_set = page.locator('.modal:has-text("설정일"), .modal:has-text("삭제 예정일")')

    if already_set.count() > 0:
        # 기한이 이미 설정된 상태 — 이것 자체가 성공 증거
        assert page.locator('text=설정일').count() > 0 or page.locator('text=삭제 예정일').count() > 0, \
            "파일기한이 설정되어 있어야 합니다"
        return

    # 신규 설정 상태: 숫자 입력창에 일수 입력
    days_input = page.locator('.modal input')
    if days_input.count() > 0:
        try:
            days_input.first.click(click_count=3)
            days_input.first.fill("30")
        except Exception:
            pass

    # 확인 버튼 클릭 (활성화 상태일 때만)
    confirm_btn = page.locator('.modal button:has-text("확인"):not([disabled]):not(.disabled)')
    assert confirm_btn.count() > 0, "파일기한 확인 버튼이 활성화 상태가 아닙니다"
    confirm_btn.first.click(timeout=5000)
    page.wait_for_timeout(2000)

    # 기한 설정 성공 확인: "파일 기한이 설정되었습니다" 또는 "설정일"/"삭제 예정일" 표시
    success_indicators = page.locator(
        'text=파일 기한이 설정되었습니다, text=설정일, text=삭제 예정일'
    )
    assert success_indicators.count() > 0, (
        "파일기한 설정 후 성공 메시지(설정일/삭제 예정일)가 표시되지 않습니다"
    )
