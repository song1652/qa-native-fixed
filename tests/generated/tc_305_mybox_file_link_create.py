"""DirectCloud: tc_305 - 마이박스 — 파일 공유 링크 생성"""
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


def test_tc_305_mybox_file_link_create(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    creds = data["directcloud"]["valid_user"]

    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # 마이박스 이동 — 사이드바는 li:has-text() 패턴 (ID 없음)
    mybox = page.locator('li:has-text("My Box")')
    assert mybox.count() > 0, "마이박스 메뉴를 찾을 수 없습니다"
    mybox.first.click(timeout=5000)
    page.wait_for_timeout(1500)
    dismiss_popups(page)

    # 파일만 선택 (폴더 제외: 폴더는 .folder 클래스 포함)
    files = page.locator('li.preview__list-item:not(.folder)')
    if files.count() == 0:
        pytest.skip("마이박스에 파일이 없어 링크 생성 테스트 불가")

    # 우클릭 → 링크생성 메뉴
    files.first.click(button='right')
    page.wait_for_timeout(800)

    link_menu = page.locator('.contextmenu-item:has-text("링크생성")')
    assert link_menu.count() > 0, "컨텍스트 메뉴에서 '링크생성' 항목을 찾을 수 없습니다"
    link_menu.first.click(timeout=5000)
    page.wait_for_timeout(2000)
    # dismiss_popups 호출 금지 — Escape가 링크 생성 모달을 닫음

    # 링크 생성 다이얼로그가 열려야 함 (링크가 자동으로 생성됨)
    # "보내기" + "취소" 버튼이 있으면 링크 생성 다이얼로그 확인
    send_or_cancel = page.locator('button:has-text("보내기"), button:has-text("취소")')
    assert send_or_cancel.count() > 0, (
        "링크 생성 다이얼로그에서 전송/취소 버튼을 찾을 수 없습니다 — 링크가 생성되지 않았을 수 있습니다"
    )
