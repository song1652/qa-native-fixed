"""
tc_CL_01_customer_login_empty_fields_validation.py
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
- 테스트 함수명: test_customer_login_empty_fields_validation
"""
from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"
EXPECTED_DIALOG_MSG = "사용자 아이디는 필수입력 입니다."


def test_customer_login_empty_fields_validation(page: Page) -> None:
    """TC CL-01: 고객 로그인 빈 필드 유효성 검증 — 빈 필드 제출 시 dialog 팝업 확인"""
    # Arrange
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 고객 탭이 기본 활성화 — 별도 탭 클릭 불필요
    expect(page.locator("#userId")).to_be_visible()
    expect(page.locator("#userPw")).to_be_visible()

    # dialog 핸들러를 버튼 클릭 전에 등록 (race condition 방지)
    dialog_messages = []

    def handle_dialog(dialog):
        dialog_messages.append(dialog.message)
        dialog.accept()

    page.on("dialog", handle_dialog)

    # Act — 필드를 비운 채 로그인 버튼 클릭
    page.locator("#userId").fill("")
    page.locator("#userPw").fill("")
    page.locator("#btnCustomerLogin").click()

    # dialog가 처리될 시간 확보
    page.wait_for_timeout(1000)

    # Assert — dialog 메시지 검증
    assert len(dialog_messages) > 0, "빈 필드 로그인 시 dialog가 표시되지 않았습니다."
    assert EXPECTED_DIALOG_MSG in dialog_messages[0], (
        f"예상 메시지 '{EXPECTED_DIALOG_MSG}' 가 실제 dialog에 없습니다. 실제: '{dialog_messages[0]}'"
    )

    # 로그인 페이지 유지 확인
    assert "login" in page.url.lower(), (
        f"빈 필드 로그인 후 예상치 못한 페이지 이동: {page.url}"
    )
