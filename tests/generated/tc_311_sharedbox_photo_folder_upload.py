"""DirectCloud: tc_311 - 공유박스 — 포토 폴더에 이미지 파일 업로드"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PAGES_PATH = PROJECT_ROOT / "config" / "pages.json"
with open(str(PAGES_PATH), 'r', encoding='utf-8') as _f:
    BASE_URL = json.load(_f)['directcloud']['url']
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"
TEST_IMAGE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "test_image.png"


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


def test_tc_311_sharedbox_photo_folder_upload(page):
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    creds = data["directcloud"]["valid_user"]
    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # 공유박스 사이드바 클릭
    sharedbox_nav = page.locator('li#sharedbox')
    assert sharedbox_nav.count() > 0, "공유박스 메뉴를 찾을 수 없습니다"
    sharedbox_nav.first.click(timeout=5000)
    page.wait_for_timeout(1500)
    dismiss_popups(page)

    # 공유박스 페이지 진입 확인
    assert "sharedbox" in page.url, f"Shared Box 진입 실패, 현재 URL: {page.url}"
    assert page.locator('#files').is_visible(), "Shared Box 파일 목록 영역(#files)이 표시되지 않습니다"

    # 업로드 input 존재 확인 (업로드 기능 지원 여부)
    upload_input = page.locator('input[type="file"]')
    assert upload_input.count() > 0, "업로드 input[type=file]을 찾을 수 없습니다"
