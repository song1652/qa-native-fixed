"""DirectCloud: tc_301 - 마이박스 — 파일에 코멘트 작성"""
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


def test_tc_301_mybox_file_comment_write(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    creds = data["directcloud"]["valid_user"]
    comment_text = data["directcloud"]["comment_text"]

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
        pytest.skip("마이박스에 파일이 없어 코멘트 테스트 불가")

    # 파일 클릭 → 우측 코멘트 패널 열기 (Escape 금지 — 패널이 닫힘)
    files.first.click()
    page.wait_for_timeout(2000)
    # dismiss_popups 호출 금지: Escape가 파일 프리뷰를 닫음

    # 코멘트 입력창 반드시 나타나야 함 (파일 상세 패널에 있음)
    comment_input = page.locator('[class*="textarea-comments-top"]')
    assert comment_input.count() > 0, "코멘트 입력창(textarea-comments-top)이 표시되지 않습니다"
    comment_input.first.fill(comment_text)

    # 확인 버튼 클릭
    submit_btn = page.locator('button:has-text("확인")')
    assert submit_btn.count() > 0, "코멘트 확인 버튼을 찾을 수 없습니다"
    submit_btn.first.click(timeout=5000)
    page.wait_for_timeout(2000)

    # 코멘트가 화면에 실제로 표시돼야 통과
    posted = page.locator(f'text={comment_text}')
    assert posted.count() > 0, f"코멘트 '{comment_text}'이 화면에 표시되지 않습니다"
    assert posted.first.is_visible(), f"코멘트 '{comment_text}'이 보이지 않습니다"
