"""
고객 로그인 빈 필드 유효성 검증
URL: https://mall.serveone.co.kr/M3/cmm/login.dev
케이스: CL-01
"""
import re

from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"

USER_ID = "#userId"
USER_PW = "#userPw"
LOGIN_BUTTON = "#btnCustomerLogin"


def test_tc_01_customer_login_empty_field_validation(page: Page):
    """아이디/비밀번호를 비워둔 채 로그인 시도 → 차단되어 로그인 페이지에 머문다."""
    # conftest page fixture가 dialog.accept() 핸들러를 이미 등록하므로 message만 수집
    dialog_messages: list[str] = []
    page.on("dialog", lambda d: dialog_messages.append(d.message))

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 고객 탭은 기본 활성 상태 — 탭 전환 불필요
    page.locator(USER_ID).fill("")
    page.locator(USER_PW).fill("")

    page.locator(LOGIN_BUTTON).click()
    page.wait_for_load_state("networkidle")

    # 로그인 페이지를 벗어나지 않아야 함
    expect(page).to_have_url(re.compile(r"login", re.IGNORECASE))
    expect(page.locator(USER_ID)).to_be_visible()
