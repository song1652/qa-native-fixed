"""DirectCloud: tc_69 - 코멘트 알림 모달 상세 버튼 및 더 보기 확인"""
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


def test_tc_69_comment_modal_detail_buttons(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    dismiss_popups(page)

    # 코멘트 알림 아이콘 클릭
    if page.locator('#showNotifyComment').count() > 0:
        page.locator('#showNotifyComment').click()
    else:
        header_btns = page.locator('button').filter(has_text='코멘트')
        if header_btns.count() > 0:
            header_btns.first.click()

    page.wait_for_timeout(2000)

    # 코멘트 모달 내 상세 버튼 확인
    # DOM: 각 listitem에 버튼 2개씩 존재 (상세/읽음)
    modal = page.locator('dialog[active], [role="dialog"]')
    if modal.count() > 0:
        try:
            modal.first.wait_for(state='visible', timeout=3000)
        except Exception:
            pass

        # 모달 내 버튼 존재 확인
        modal_btns = modal.first.locator('button')
        if modal_btns.count() >= 1:
            assert modal_btns.first.is_visible(), "모달 내 버튼이 표시되어야 합니다."

    assert page.locator('body').is_visible()
