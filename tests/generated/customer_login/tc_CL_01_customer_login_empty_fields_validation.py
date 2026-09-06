"""
tc_CL_01_customer_login_empty_fields_validation.py
- 고객 로그인 빈 필드 유효성 검증
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
- 테스트 함수명: test_customer_login_empty_fields_validation
"""
from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"
EXPECTED_DIALOG_MSG = "사용자 아이디는 필수입력 입니다."


def test_customer_login_empty_fields_validation(page: Page) -> None:
    """CL_01: 고객 로그인 빈 필드 → 다이얼로그 팝업, 페이지 이동 없음"""
    # Dialog 핸들러를 goto 이전에 등록 (race condition 방지)
    dialog_messages = []

    def handle_dialog(dialog):
        dialog_messages.append(dialog.message)
        dialog.dismiss()

    page.on("dialog", handle_dialog)

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 필드 비워둔 채로 고객 로그인 버튼 클릭
    page.locator("#btnCustomerLogin").click()
    page.wait_for_timeout(1000)

    # 다이얼로그 발생 확인
    assert dialog_messages, "로그인 버튼 클릭 시 다이얼로그가 표시되어야 합니다"
    assert any("사용자 아이디는 필수입력 입니다" in msg for msg in dialog_messages), (
        f"예상 메시지 없음. 실제: {dialog_messages}"
    )

    # 페이지 이동 없이 로그인 페이지 유지
    expect(page).to_have_url(BASE_URL)
