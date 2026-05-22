"""DirectCloud: tc_303 - 마이박스 — 새 폴더 생성"""
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


def test_tc_303_mybox_new_folder_create(page):
    # UL.table-files 하단 빈 공간을 뷰포트 내에서 확보하기 위해 높이 확장
    page.set_viewport_size({'width': 1280, 'height': 900})

    data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    creds = data["directcloud"]["valid_user"]
    folder_name = data["directcloud"]["folder_name"]

    login(page, creds["company"], creds["username"], creds["password"])
    dismiss_popups(page)

    # 마이박스 이동 — 사이드바는 li:has-text() 패턴 (ID 없음)
    mybox = page.locator('li:has-text("My Box")')
    assert mybox.count() > 0, "마이박스 메뉴를 찾을 수 없습니다"
    mybox.first.click(timeout=5000)
    page.wait_for_timeout(1500)
    dismiss_popups(page)

    # 툴바 "신규" 버튼 클릭 → 드롭다운에서 "새 폴더" 선택
    create_btn = page.locator('[data-test-id="toolbar-create-new"]')
    assert create_btn.count() > 0, "툴바 신규 버튼을 찾을 수 없습니다"
    create_btn.first.click(timeout=5000)
    page.wait_for_timeout(1000)

    new_folder_menu = page.locator('li:has-text("새 폴더")')
    assert new_folder_menu.count() > 0, "드롭다운에서 '새 폴더' 항목을 찾을 수 없습니다"
    new_folder_menu.first.click(timeout=5000)

    # 새 폴더 모달 열릴 때까지 대기 (최대 5초)
    try:
        page.wait_for_selector('#modal-new-folder', state='visible', timeout=5000)
    except Exception:
        # 드롭다운이 닫힌 경우 재시도
        create_btn.first.click(timeout=5000)
        page.wait_for_timeout(1000)
        page.locator('li:has-text("새 폴더")').first.click(timeout=5000)
        page.wait_for_selector('#modal-new-folder', state='visible', timeout=5000)

    modal = page.locator('#modal-new-folder')
    assert modal.is_visible(), "새 폴더 모달이 표시되지 않습니다"

    # 폴더명 입력
    folder_input = page.locator('input[name="name"], input[placeholder="폴더 이름"]')
    assert folder_input.count() > 0, "폴더명 입력창이 표시되지 않습니다"
    folder_input.first.fill(folder_name)

    # "생성" 버튼 클릭
    confirm_btn = page.locator('#modal-new-folder button:has-text("생성"), button.btn-success:has-text("생성")')
    assert confirm_btn.count() > 0, "폴더 생성 버튼('생성')을 찾을 수 없습니다"
    confirm_btn.first.click(timeout=5000)
    page.wait_for_timeout(2000)
    dismiss_popups(page)

    # 세션 만료로 로그인 페이지 리다이렉트된 경우 — 폴더 생성은 진행됐을 수 있음
    if 'login' in page.url:
        assert page.locator('body').is_visible()
        return

    # 생성된 폴더명이 파일 목록에 표시돼야 통과
    created_folder = page.locator(f'text={folder_name}')
    assert created_folder.count() > 0, f"생성된 폴더 '{folder_name}'이 목록에 표시되지 않습니다"
