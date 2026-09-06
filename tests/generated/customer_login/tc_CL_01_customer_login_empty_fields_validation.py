"""
자동 생성된 Playwright 테스트 코드
URL: https://mall.serveone.co.kr/M3/cmm/login.dev
케이스: customer_login_empty_fields_validation (CL_01)

Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"


def test_customer_login_empty_fields_validation(page: Page):
    """고객 로그인 빈 필드 유효성 검증 — 빈 필드 제출 시 alert 팝업 확인"""
    dialog_messages = []

    def handle_dialog(dialog):
        dialog_messages.append(dialog.message)
        dialog.dismiss()

    page.on("dialog", handle_dialog)

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 아이디/비밀번호 필드 비워두기 (기본값 빈 필드)
    page.locator("#userId").fill("")
    page.locator("#userPw").fill("")

    # 로그인 버튼 클릭
    page.locator("#btnCustomerLogin").click()

    # dialog 처리 대기
    page.wait_for_timeout(1000)

    # 검증: dialog에 필수입력 메시지 포함
    assert dialog_messages, "dialog 팝업이 표시되지 않았습니다"
    assert any(
        "사용자 아이디는 필수입력 입니다" in msg for msg in dialog_messages
    ), f"예상 메시지가 없음. 실제: {dialog_messages}"

    # 페이지 이동 없음 확인
    expect(page).to_have_url(BASE_URL)
