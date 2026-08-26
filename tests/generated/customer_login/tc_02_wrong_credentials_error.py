"""
tc_02_wrong_credentials_error.py
고객 로그인 잘못된 자격증명 에러 — 존재하지 않는 계정으로 로그인 시도.
"""
import json
import re
from pathlib import Path

from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"

# 고객 로그인 폼 셀렉터
USER_ID = "#userId"
USER_PW = "#userPw"
LOGIN_BUTTON = "#btnCustomerLogin"

TEST_DATA_PATH = Path(__file__).parent.parent.parent.parent / "config" / "test_data.json"
test_data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))


def test_wrong_credentials_error(page: Page):
    """잘못된 아이디/비밀번호로는 로그인에 실패하고 로그인 페이지에 머문다."""
    # conftest.py의 page fixture가 이미 dialog.accept() 핸들러를 등록하므로
    # 여기서는 alert 메시지만 수집한다 (dismiss/accept 중복 처리 시 예외 발생).
    dialog_messages: list[str] = []
    page.on("dialog", lambda dialog: dialog_messages.append(dialog.message))

    login_data = test_data["serveone"]["login"]

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 고객 탭은 기본 활성 상태이므로 탭 전환 없이 진행
    page.locator(USER_ID).fill(login_data["invalid_customer_id"])
    page.locator(USER_PW).fill(login_data["invalid_password"])

    page.locator(LOGIN_BUTTON).click()
    page.wait_for_load_state("networkidle")

    # 검증: 로그인에 실패해 로그인 페이지를 벗어나지 않는다
    expect(page).to_have_url(re.compile(r"login", re.IGNORECASE))
    expect(page.locator(USER_ID)).to_be_visible()
