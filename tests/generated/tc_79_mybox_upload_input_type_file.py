"""DirectCloud: tc_79 - My Box 파일 업로드 input 속성 검증"""
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


def test_tc_79_mybox_upload_input_type_file(page):
    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    user = data["directcloud"]["valid_user"]
    login(page, user["company"], user["username"], user["password"])
    page.wait_for_load_state('networkidle')
    dismiss_popups(page)

    # MyBox로 이동 (업로드 버튼은 MyBox 페이지에만 존재)
    mybox_nav = page.locator('li:has-text("My Box")')
    if mybox_nav.count() > 0:
        mybox_nav.first.click()
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)
        dismiss_popups(page)

    upload_input = page.locator('#fileuploadBtn')
    if upload_input.count() > 0:
        input_type = upload_input.first.get_attribute('type') or ''
        assert input_type == 'file', f"업로드 input의 type이 'file'이어야 합니다. 실제: {input_type}"
    else:
        # input[type=file] 일반 selector로 확인
        file_inputs = page.locator('input[type="file"]')
        assert file_inputs.count() > 0, "파일 업로드 input[type=file]이 존재해야 합니다."
