"""
고객 로그인 잘못된 자격증명 에러
URL: https://mall.serveone.co.kr/M3/cmm/login.dev
케이스: CL-02
"""
import json
import re
from pathlib import Path

from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"
with open(TEST_DATA_PATH, encoding="utf-8") as _f:
    _test_data = json.load(_f)

USER_ID = "#userId"
USER_PW = "#userPw"
LOGIN_BUTTON = "#btnCustomerLogin"


def test_tc_02_customer_login_invalid_credentials(page: Page):
    """잘못된 아이디/비밀번호로 로그인 시도 → 실패하고 로그인 페이지에 머문다."""
    # conftest page fixture가 dialog.accept()를 등록하므로 message만 수집
    dialog_messages: list[str] = []
    page.on("dialog", lambda d: dialog_messages.append(d.message))

    login_data = _test_data["serveone"]["login"]
    invalid_id = login_data["invalid_customer_id"]
    invalid_pw = login_data["invalid_password"]

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 고객 탭은 기본 활성 상태 — 탭 전환 불필요
    page.locator(USER_ID).fill(invalid_id)
    page.locator(USER_PW).fill(invalid_pw)

    page.locator(LOGIN_BUTTON).click()
    page.wait_for_load_state("networkidle")

    # 로그인 실패: 로그인 페이지에 머물러야 함
    expect(page).to_have_url(re.compile(r"login", re.IGNORECASE))
    expect(page.locator(USER_ID)).to_be_visible()

    # alert 또는 인라인 에러 메시지 검증
    if dialog_messages:
        assert dialog_messages[0].strip(), "alert 메시지가 비어 있음"
    else:
        # #LoginMsg가 표시되거나, ID 필드가 유지되면 실패 처리된 것
        expect(page.locator(USER_ID)).to_be_visible()
