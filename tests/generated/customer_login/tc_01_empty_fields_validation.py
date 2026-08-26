"""
tc_01_empty_fields_validation.py
고객 로그인 빈 필드 유효성 검증 — 아이디/비밀번호를 비운 채 로그인 시도.
"""
import re

from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"

# 고객 로그인 폼 셀렉터
USER_ID = "#userId"
USER_PW = "#userPw"
LOGIN_BUTTON = "#btnCustomerLogin"


def test_empty_fields_validation(page: Page):
    """아이디/비밀번호가 비어 있으면 로그인되지 않고 로그인 페이지에 머문다."""
    # conftest.py의 page fixture가 이미 dialog.accept() 핸들러를 등록하므로
    # 여기서는 alert 메시지만 수집한다 (dismiss/accept 중복 처리 시 예외 발생).
    dialog_messages: list[str] = []
    page.on("dialog", lambda dialog: dialog_messages.append(dialog.message))

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 고객 탭은 기본 활성 상태이므로 탭 전환 없이 진행
    page.locator(USER_ID).fill("")
    page.locator(USER_PW).fill("")

    page.locator(LOGIN_BUTTON).click()
    page.wait_for_load_state("networkidle")

    # 검증: 로그인 페이지를 벗어나지 않는다 (alert 또는 인라인 에러로 차단됨)
    expect(page).to_have_url(re.compile(r"login", re.IGNORECASE))
    expect(page.locator(USER_ID)).to_be_visible()
